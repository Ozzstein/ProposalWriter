import type {
  AgentGraph,
  MemoryStore,
  ProjectSummary,
} from "@pw/shared";

const BASE = "/api";

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${url}`);
  }
  return (await res.json()) as T;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${url}`);
  }
  return (await res.json()) as T;
}

export async function listProjects(): Promise<ProjectSummary[]> {
  const data = await getJson<{ items: ProjectSummary[] }>(`${BASE}/projects`);
  return data.items;
}

export async function getProject(name: string): Promise<ProjectSummary> {
  return getJson<ProjectSummary>(
    `${BASE}/projects/${encodeURIComponent(name)}`,
  );
}

export async function getMemory(
  project: string,
  store: MemoryStore,
  opts: { offset?: number; limit?: number } = {},
): Promise<{
  store: MemoryStore;
  total: number;
  offset: number;
  limit: number;
  items: unknown[];
  overrides: Array<[string, unknown[]]> | null;
}> {
  const qs = new URLSearchParams();
  if (opts.offset !== undefined) qs.set("offset", String(opts.offset));
  if (opts.limit !== undefined) qs.set("limit", String(opts.limit));
  const q = qs.toString();
  return getJson(
    `${BASE}/projects/${encodeURIComponent(project)}/memory/${store}${
      q ? `?${q}` : ""
    }`,
  );
}

export async function postOverride(
  project: string,
  store: MemoryStore,
  body: { target_id: string; status?: string; note?: string; type?: "override" | "note" },
): Promise<{ ok: boolean }> {
  return postJson(
    `${BASE}/projects/${encodeURIComponent(project)}/memory/${store}/override`,
    body,
  );
}

export async function getAgentGraph(): Promise<AgentGraph> {
  return getJson<AgentGraph>(`${BASE}/agents/graph`);
}

export async function getAgentFile(relativePath: string): Promise<string> {
  const qs = new URLSearchParams({ path: relativePath });
  const data = await getJson<{ body: string }>(`${BASE}/agents/file?${qs}`);
  return data.body;
}

export type StageName =
  | "start-proposal"
  | "parse-call"
  | "research"
  | "write-proposal"
  | "review"
  | "external-review"
  | "gate-check"
  | "pipeline-status";

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

export async function launchStage(
  project: string,
  stage: StageName,
  body: { args?: string; resume?: string } = {},
): Promise<{ ok: boolean; session: SessionRecord }> {
  return postJson(
    `${BASE}/projects/${encodeURIComponent(project)}/stages/${stage}`,
    body,
  );
}

export async function listSessions(): Promise<SessionRecord[]> {
  const data = await getJson<{ items: SessionRecord[] }>(`${BASE}/sessions`);
  return data.items;
}

export async function stopSession(id: string): Promise<{ ok: boolean }> {
  return postJson(`${BASE}/sessions/${encodeURIComponent(id)}/stop`, {});
}
