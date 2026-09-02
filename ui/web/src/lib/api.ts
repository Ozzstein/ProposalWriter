import type {
  AgentGraph,
  GateResult,
  OverrideRecord,
  GraphEdge,
  GraphNode,
  InboxItem,
  JobRecord,
  MemoryStore,
  NodeDetail,
  PipelineEvent,
  ProjectSummary,
  RunRecord,
  StageDef,
} from "@pw/shared";

const BASE = "/api";

async function handle<T>(res: Response, url: string): Promise<T> {
  if (!res.ok) {
    let detail = "";
    try {
      detail = ((await res.json()) as { detail?: string }).detail ?? "";
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status} ${res.statusText}${detail ? `: ${detail}` : ""} (${url})`);
  }
  return (await res.json()) as T;
}

async function getJson<T>(url: string): Promise<T> {
  return handle<T>(await fetch(url), url);
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  return handle<T>(res, url);
}

const enc = encodeURIComponent;

// ---------------------------------------------------------------- projects
export async function listProjects(): Promise<ProjectSummary[]> {
  return (await getJson<{ items: ProjectSummary[] }>(`${BASE}/projects`)).items;
}

export async function getProject(id: string): Promise<ProjectSummary> {
  return getJson(`${BASE}/projects/${enc(id)}`);
}

export interface CreateProjectBody {
  name: string;
  funder?: string;
  mechanism?: string;
  topic?: string;
  deadline?: string;
  hypothesis?: string;
  context_md?: string;
  pack?: string;
  skip_ideation?: boolean;
}

export async function createProject(body: CreateProjectBody): Promise<ProjectSummary> {
  return postJson(`${BASE}/projects`, body);
}

export async function uploadInputs(project: string, files: File[], subdir = ""): Promise<{ saved: string[] }> {
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  fd.append("subdir", subdir);
  const url = `${BASE}/projects/${enc(project)}/inputs`;
  return handle(await fetch(url, { method: "POST", body: fd }), url);
}

export async function getProjectFile(project: string, path: string): Promise<string> {
  const qs = new URLSearchParams({ path });
  return (await getJson<{ body: string }>(`${BASE}/projects/${enc(project)}/files?${qs}`)).body;
}

export async function getDocument(project: string, kind: string): Promise<GraphNode> {
  return getJson(`${BASE}/projects/${enc(project)}/documents/${enc(kind)}`);
}

export async function listSections(project: string): Promise<GraphNode[]> {
  return (await getJson<{ items: GraphNode[] }>(`${BASE}/projects/${enc(project)}/sections`)).items;
}

// ---------------------------------------------------------------- graph / memory
export async function getMemory(
  project: string,
  store: MemoryStore,
  opts: { offset?: number; limit?: number } = {},
): Promise<{
  store: MemoryStore;
  total: number;
  offset: number;
  limit: number;
  items: Record<string, unknown>[];
  overrides: Array<[string, OverrideRecord[]]> | null;
}> {
  const qs = new URLSearchParams();
  if (opts.offset !== undefined) qs.set("offset", String(opts.offset));
  if (opts.limit !== undefined) qs.set("limit", String(opts.limit));
  const q = qs.toString();
  return getJson(`${BASE}/projects/${enc(project)}/memory/${store}${q ? `?${q}` : ""}`);
}

export async function postOverride(
  project: string,
  store: MemoryStore,
  body: { target_id: string; status?: string; note?: string; type?: "override" | "note" },
): Promise<{ ok: boolean }> {
  return postJson(`${BASE}/projects/${enc(project)}/memory/${store}/override`, body);
}

export async function listNodes(
  project: string,
  params: { type?: string; status?: string; q?: string; limit?: number } = {},
): Promise<{ items: GraphNode[]; summary: Record<string, number> }> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined) qs.set(k, String(v));
  return getJson(`${BASE}/projects/${enc(project)}/graph?${qs}`);
}

export async function listEdges(project: string, type?: string): Promise<GraphEdge[]> {
  const qs = type ? `?type=${enc(type)}` : "";
  return (await getJson<{ items: GraphEdge[] }>(`${BASE}/projects/${enc(project)}/graph/edges${qs}`)).items;
}

export async function getNode(project: string, id: string): Promise<NodeDetail> {
  return getJson(`${BASE}/projects/${enc(project)}/graph/${enc(id)}`);
}

// ---------------------------------------------------------------- gates / stages / runs
export async function runGate(project: string, gate: string): Promise<GateResult> {
  return postJson(`${BASE}/projects/${enc(project)}/gates/${enc(gate)}`, {});
}

export async function listStages(): Promise<StageDef[]> {
  return (await getJson<{ items: StageDef[] }>(`${BASE}/stages`)).items;
}

export async function startRun(
  project: string,
  stage: string,
  body: { flags?: Record<string, unknown>; resume?: string; force?: boolean } = {},
): Promise<RunRecord> {
  return postJson(`${BASE}/projects/${enc(project)}/stages/${enc(stage)}`, body);
}

export async function listRuns(project?: string): Promise<RunRecord[]> {
  const qs = project ? `?project=${enc(project)}` : "";
  return (await getJson<{ items: RunRecord[] }>(`${BASE}/runs${qs}`)).items;
}

export async function getRun(id: string): Promise<{ run: RunRecord; jobs: JobRecord[]; costs: Record<string, unknown>[] }> {
  return getJson(`${BASE}/runs/${enc(id)}`);
}

export async function stopRun(id: string): Promise<{ stopped: string }> {
  return postJson(`${BASE}/runs/${enc(id)}/stop`, {});
}

// ---------------------------------------------------------------- inbox
export async function listInbox(project?: string, status: "pending" | "all" = "pending"): Promise<InboxItem[]> {
  const qs = new URLSearchParams({ status });
  if (project) qs.set("project", project);
  return (await getJson<{ items: InboxItem[] }>(`${BASE}/inbox?${qs}`)).items;
}

export async function answerInbox(id: string, answer: Record<string, unknown>): Promise<InboxItem> {
  return postJson(`${BASE}/inbox/${enc(id)}/answer`, { answer });
}

// ---------------------------------------------------------------- events / costs / agents
export async function listEvents(project?: string, since = 0, limit = 500): Promise<PipelineEvent[]> {
  const qs = new URLSearchParams({ since: String(since), limit: String(limit) });
  if (project) qs.set("project", project);
  return (await getJson<{ items: PipelineEvent[] }>(`${BASE}/events?${qs}`)).items;
}

export async function getCosts(project?: string): Promise<{ total_usd: number; by_agent: Record<string, number>; items: Record<string, unknown>[] }> {
  const qs = project ? `?project=${enc(project)}` : "";
  return getJson(`${BASE}/costs${qs}`);
}

export async function getAgentGraph(): Promise<AgentGraph> {
  return getJson(`${BASE}/agents/graph`);
}

export async function getAgentFile(relativePath: string): Promise<string> {
  const qs = new URLSearchParams({ path: relativePath });
  return (await getJson<{ body: string }>(`${BASE}/agents/file?${qs}`)).body;
}
