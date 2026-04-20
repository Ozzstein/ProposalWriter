import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { COMMANDS_DIR, REPO_ROOT, SERVER_DATA_DIR } from "./paths.js";
import { appendEvent } from "./emit.js";

export type StageName =
  | "start-proposal"
  | "parse-call"
  | "research"
  | "write-proposal"
  | "review"
  | "external-review"
  | "gate-check"
  | "pipeline-status";

export const STAGES: StageName[] = [
  "start-proposal",
  "parse-call",
  "research",
  "write-proposal",
  "review",
  "external-review",
  "gate-check",
  "pipeline-status",
];

export interface SessionRecord {
  id: string;
  sdk_session_id?: string;
  project: string;
  stage: StageName;
  args?: string;
  started_at: string;
  ended_at?: string;
  status: "running" | "completed" | "failed" | "stopped";
  error?: string;
}

const SESSIONS_FILE = path.join(SERVER_DATA_DIR, "sessions.jsonl");
const running = new Map<string, { abort: AbortController; rec: SessionRecord }>();

async function ensureDir(dir: string): Promise<void> {
  await fsp.mkdir(dir, { recursive: true });
}

async function appendSession(rec: SessionRecord): Promise<void> {
  await ensureDir(SERVER_DATA_DIR);
  await fsp.appendFile(SESSIONS_FILE, JSON.stringify(rec) + "\n", "utf8");
}

export async function listSessions(): Promise<SessionRecord[]> {
  try {
    const raw = await fsp.readFile(SESSIONS_FILE, "utf8");
    // Fold by id: last-write-wins for status updates.
    const byId = new Map<string, SessionRecord>();
    for (const line of raw.split("\n")) {
      if (!line.trim()) continue;
      try {
        const rec = JSON.parse(line) as SessionRecord;
        byId.set(rec.id, rec);
      } catch {
        /* skip bad line */
      }
    }
    // Merge in-memory running state (source of truth for live status)
    for (const [id, v] of running) byId.set(id, v.rec);
    return Array.from(byId.values()).sort((a, b) =>
      b.started_at.localeCompare(a.started_at),
    );
  } catch {
    return Array.from(running.values()).map((v) => v.rec);
  }
}

async function readCommandPrompt(stage: StageName): Promise<string> {
  const file = path.join(COMMANDS_DIR, `${stage}.md`);
  return fsp.readFile(file, "utf8");
}

function commandDefinesProjectVar(prompt: string): boolean {
  return /\{project\}/i.test(prompt);
}

function buildPrompt(
  commandBody: string,
  project: string,
  args?: string,
): string {
  let body = commandBody;
  if (commandDefinesProjectVar(body)) {
    body = body.replace(/\{project\}/gi, project);
  }
  const header = [
    `You are working on project: \`${project}\``,
    `Project root: \`runs/${project}/\``,
    args ? `Arguments: ${args}` : "",
  ]
    .filter(Boolean)
    .join("\n");
  const argsLine = args ? `\n\n## Arguments\n\n${args}\n` : "";
  return `${header}\n\n---\n\n${body}${argsLine}`;
}

interface LaunchOptions {
  project: string;
  stage: StageName;
  args?: string;
  resume?: string; // sdk session id to resume
}

export async function launchStage(opts: LaunchOptions): Promise<SessionRecord> {
  const projectDir = path.join(REPO_ROOT, "runs", opts.project);
  if (!fs.existsSync(projectDir)) {
    throw new Error(`Project not found: runs/${opts.project}`);
  }

  const commandBody = await readCommandPrompt(opts.stage);
  const prompt = buildPrompt(commandBody, opts.project, opts.args);

  const id = randomUUID();
  const rec: SessionRecord = {
    id,
    project: opts.project,
    stage: opts.stage,
    args: opts.args,
    started_at: new Date().toISOString(),
    status: "running",
  };
  const abort = new AbortController();
  running.set(id, { abort, rec });
  await appendSession(rec);

  // Fire + run asynchronously; SSE feed surfaces progress.
  void runStage(id, prompt, opts, abort.signal).catch(() => {
    /* already reported via status */
  });

  return rec;
}

export async function stopSession(id: string): Promise<boolean> {
  const entry = running.get(id);
  if (!entry) return false;
  entry.abort.abort();
  entry.rec.status = "stopped";
  entry.rec.ended_at = new Date().toISOString();
  await appendSession(entry.rec);
  running.delete(id);
  return true;
}

async function runStage(
  id: string,
  prompt: string,
  opts: LaunchOptions,
  signal: AbortSignal,
): Promise<void> {
  const entry = running.get(id);
  if (!entry) return;
  const rec = entry.rec;
  try {
    // Lazy-load the SDK so the server still boots if the package is missing.
    type SdkMessage = {
      type?: string;
      session_id?: string;
      message?: unknown;
      subtype?: string;
    };
    type QueryFn = (opts: {
      prompt: string;
      options?: Record<string, unknown>;
    }) => AsyncIterable<SdkMessage>;

    let query: QueryFn;
    try {
      const mod = (await import("@anthropic-ai/claude-agent-sdk")) as {
        query: QueryFn;
      };
      query = mod.query;
    } catch (e) {
      throw new Error(
        `@anthropic-ai/claude-agent-sdk not installed: ${
          e instanceof Error ? e.message : String(e)
        }. Install it in ui/server to enable stage launches.`,
      );
    }

    const projectDir = path.join(REPO_ROOT, "runs", opts.project);
    const iterator = query({
      prompt,
      options: {
        cwd: projectDir,
        ...(opts.resume ? { resume: opts.resume } : {}),
      },
    });

    await appendEvent({
      session_id: id,
      hook: "SdkStream",
      tool_name: "stage:start",
      project_hint: opts.project,
      extra: { stage: opts.stage, args: opts.args ?? null },
    });

    for await (const msg of iterator) {
      if (signal.aborted) break;
      if (msg.session_id && !rec.sdk_session_id) {
        rec.sdk_session_id = msg.session_id;
      }
      await appendEvent({
        session_id: rec.sdk_session_id ?? id,
        hook: "SdkStream",
        tool_name: msg.type ?? "message",
        project_hint: opts.project,
        extra: summarizeMessage(msg),
      });
    }

    if (signal.aborted) {
      rec.status = "stopped";
    } else {
      rec.status = "completed";
    }
  } catch (err) {
    rec.status = "failed";
    rec.error = err instanceof Error ? err.message : String(err);
    await appendEvent({
      session_id: rec.sdk_session_id ?? id,
      hook: "SdkStream",
      tool_name: "stage:error",
      project_hint: opts.project,
      extra: { error: rec.error },
    });
  } finally {
    rec.ended_at = new Date().toISOString();
    await appendSession(rec);
    running.delete(id);
  }
}

function summarizeMessage(msg: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const key of ["type", "subtype"]) {
    if (msg[key] !== undefined) out[key] = msg[key];
  }
  // Keep payload small — don't replay the entire SDK message.
  if (typeof msg.message === "object" && msg.message !== null) {
    const m = msg.message as Record<string, unknown>;
    if (typeof m.role === "string") out.role = m.role;
    if (Array.isArray(m.content)) {
      out.content_kinds = (m.content as Array<Record<string, unknown>>)
        .map((c) => (typeof c.type === "string" ? c.type : "unknown"))
        .slice(0, 8);
    }
  }
  return out;
}
