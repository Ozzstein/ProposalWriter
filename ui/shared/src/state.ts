export type StageName =
  | "call_parsing"
  | "research"
  | "writing"
  | "review"
  | "template_population"
  | "external_review";

export type GateName = "scope" | "evidence" | "draft" | "submission";

export interface StageStatus {
  status: "pending" | "in_progress" | "complete" | "failed";
  completed_at?: string;
  started_at?: string;
  note?: string;
  [k: string]: unknown;
}

export interface GateStatus {
  passed: boolean;
  checked_at?: string;
  note?: string;
}

export interface ProjectState {
  project_name: string;
  project_title?: string;
  funding_agency?: string;
  mechanism?: string;
  created_at?: string;
  deadline?: string;
  applicant?: string;
  stages: Partial<Record<StageName, StageStatus>>;
  gates: Partial<Record<GateName, GateStatus>>;
  [k: string]: unknown;
}

export interface MemoryCounts {
  evidence: number;
  claims: number;
  decisions: number;
  tasks: number;
  feedback: number;
  overrides: number;
}

export interface ProjectSummary {
  name: string;
  state: ProjectState;
  memory: MemoryCounts;
}
