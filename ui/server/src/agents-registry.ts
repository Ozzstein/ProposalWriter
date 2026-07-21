import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import type { AgentEdge, AgentGraph, AgentKind, AgentNode } from "@pw/shared";
import { AGENTS_DIR, COMMANDS_DIR, REPO_ROOT } from "./paths.js";
import { fileExists } from "./jsonl.js";

const WORKER_KINDS: Record<string, AgentKind> = {
  retrievers: "retriever",
  synthesizers: "synthesizer",
  writers: "writer",
  reviewers: "reviewer",
  finance: "worker",
  business_plan: "worker",
  graphics: "worker",
};

function titleFromFilename(filename: string): string {
  return path
    .basename(filename, ".md")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function firstHeading(body: string): string | undefined {
  const m = body.match(/^#\s+(.+)$/m);
  return m?.[1]?.trim();
}

function firstParagraphAfterHeading(
  body: string,
  heading: string,
): string | undefined {
  const re = new RegExp(`##\\s+${heading}\\s*\\n+([^\\n]+)`, "i");
  const m = body.match(re);
  return m?.[1]?.trim();
}

function inferModel(body: string): AgentNode["model"] {
  const m = body.match(/model[:\s]+(haiku|sonnet|opus)/i);
  return (m?.[1]?.toLowerCase() as AgentNode["model"]) ?? undefined;
}

async function listMarkdown(dir: string): Promise<string[]> {
  if (!(await fileExists(dir))) return [];
  const entries = await readdir(dir, { withFileTypes: true });
  return entries
    .filter((e) => e.isFile() && e.name.endsWith(".md"))
    .map((e) => path.join(dir, e.name));
}

function toRelative(abs: string): string {
  return path.relative(REPO_ROOT, abs);
}

async function parseAgentFile(
  filePath: string,
  kind: AgentKind,
  idPrefix: string,
): Promise<AgentNode> {
  const body = await readFile(filePath, "utf8");
  const name = path.basename(filePath, ".md");
  const heading = firstHeading(body);
  const mission =
    firstParagraphAfterHeading(body, "Mission") ??
    firstParagraphAfterHeading(body, "Responsibilities") ??
    "";
  return {
    id: `${idPrefix}/${name}`,
    kind,
    title: heading ?? titleFromFilename(filePath),
    description: mission.slice(0, 280),
    model: inferModel(body),
    file: toRelative(filePath),
  };
}

/** Find references to worker agent files inside an orchestrator body. */
function findWorkerReferences(body: string): string[] {
  const ids: string[] = [];
  const pattern = /agents\/workers\/(retrievers|synthesizers|writers|reviewers|finance|business_plan|graphics)\/([a-z0-9_]+)\.md/gi;
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(body)) !== null) {
    ids.push(`workers/${m[1]}/${m[2]}`);
  }
  const boldPattern = /\*\*([a-z0-9_]+)\*\*\s*\(model:\s*(haiku|sonnet|opus)\)/gi;
  while ((m = boldPattern.exec(body)) !== null) {
    ids.push(`ref:${m[1]}`);
  }
  return Array.from(new Set(ids));
}

function findOrchestratorReference(body: string): string | null {
  const m = body.match(/agents\/orchestrators\/([a-z0-9_]+)\.md/i);
  if (!m) return null;
  return `orchestrators/${m[1]}`;
}

let cached: AgentGraph | null = null;

export async function buildAgentGraph(): Promise<AgentGraph> {
  if (cached) return cached;

  const nodes: AgentNode[] = [];
  const edges: AgentEdge[] = [];

  // Commands
  const commandFiles = await listMarkdown(COMMANDS_DIR);
  for (const file of commandFiles) {
    const name = path.basename(file, ".md");
    const body = await readFile(file, "utf8");
    nodes.push({
      id: `commands/${name}`,
      kind: "command",
      title: `/${name}`,
      description: body.split("\n").slice(0, 3).join(" ").slice(0, 280),
      file: toRelative(file),
    });
    const orch = findOrchestratorReference(body);
    if (orch) {
      edges.push({ from: `commands/${name}`, to: orch });
    }
  }

  // Orchestrators
  const orchDir = path.join(AGENTS_DIR, "orchestrators");
  const orchFiles = await listMarkdown(orchDir);
  const orchestratorIds = new Set<string>();
  for (const file of orchFiles) {
    const node = await parseAgentFile(file, "orchestrator", "orchestrators");
    nodes.push(node);
    orchestratorIds.add(node.id);
  }

  // Workers
  const workerIdByName = new Map<string, string>();
  const subdirs = await readdir(path.join(AGENTS_DIR, "workers"), {
    withFileTypes: true,
  }).catch(() => []);
  for (const sub of subdirs) {
    if (!sub.isDirectory()) continue;
    const kind = WORKER_KINDS[sub.name] ?? "worker";
    const workerFiles = await listMarkdown(
      path.join(AGENTS_DIR, "workers", sub.name),
    );
    for (const file of workerFiles) {
      const node = await parseAgentFile(file, kind, `workers/${sub.name}`);
      nodes.push(node);
      const shortName = path.basename(file, ".md");
      workerIdByName.set(shortName, node.id);
    }
  }

  // Orchestrator → worker edges
  for (const file of orchFiles) {
    const orchId = `orchestrators/${path.basename(file, ".md")}`;
    const body = await readFile(file, "utf8");
    const refs = findWorkerReferences(body);
    const seen = new Set<string>();
    for (const ref of refs) {
      let targetId: string | null = null;
      if (ref.startsWith("workers/")) {
        targetId = ref;
      } else if (ref.startsWith("ref:")) {
        const shortName = ref.slice(4);
        targetId = workerIdByName.get(shortName) ?? null;
      }
      if (!targetId) continue;
      if (seen.has(targetId)) continue;
      seen.add(targetId);
      edges.push({ from: orchId, to: targetId });
    }
  }

  cached = { nodes, edges };
  return cached;
}

export function invalidateAgentGraph(): void {
  cached = null;
}

export async function readAgentFile(relativePath: string): Promise<string | null> {
  const abs = path.resolve(REPO_ROOT, relativePath);
  if (!abs.startsWith(REPO_ROOT)) return null;
  if (!(await fileExists(abs))) return null;
  return readFile(abs, "utf8");
}
