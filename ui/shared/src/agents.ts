export type AgentKind =
  | "stage"
  | "retriever"
  | "synthesizer"
  | "writer"
  | "reviewer"
  | "modeler"
  | "renderer"
  | "interviewer"
  | "planner";

export type AgentModel = "fast" | "balanced" | "reasoning";

export interface AgentNode {
  /** "stages/research" or "agents/novelty_mapper" */
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
