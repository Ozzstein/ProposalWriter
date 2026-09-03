export type MemoryStore =
  | "evidence"
  | "claims"
  | "gaps"
  | "anchors"
  | "sections"
  | "findings"
  | "figures"
  | "decisions"
  | "feedback"
  | "tasks"
  | "overrides";

export interface GraphNode {
  id: string;
  type: string;
  scope: "project" | "workspace";
  project_id?: string | null;
  status: string;
  version: number;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  data: Record<string, unknown>;
}

export interface GraphEdge {
  src: string;
  dst: string;
  type: string;
  created_by?: string | null;
  created_at: string;
  data: Record<string, unknown>;
}

export interface NodeDetail {
  node: GraphNode;
  out: GraphEdge[];
  in: GraphEdge[];
  provenance: { nodes: GraphNode[]; edges: GraphEdge[] };
  versions: Array<{ version: number; updated_at: string }>;
}

export interface OverrideRecord {
  type: "override" | "note";
  target_id: string;
  target_store: MemoryStore;
  status?: string;
  note?: string;
  ts: string;
  user?: string;
}
