export type AgentKind =
  | "command"
  | "orchestrator"
  | "retriever"
  | "synthesizer"
  | "writer"
  | "reviewer"
  | "worker";

export type AgentModel = "haiku" | "sonnet" | "opus";

export interface AgentNode {
  /** Stable id, e.g. "orchestrators/research_orchestrator" or "commands/research" */
  id: string;
  kind: AgentKind;
  title: string;
  description: string;
  model?: AgentModel;
  /** Repo-relative path; used for click-through to raw markdown */
  file: string;
}

export interface AgentEdge {
  from: string;
  to: string;
  phase?: string;
}

export interface AgentGraph {
  nodes: AgentNode[];
  edges: AgentEdge[];
}
