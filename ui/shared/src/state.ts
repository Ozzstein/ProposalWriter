export type StageKey =
  | "ideation"
  | "call_parsing"
  | "research"
  | "writing"
  | "finance"
  | "figures"
  | "business_plan"
  | "review"
  | "external_review"
  | "export";

export type GateName = "scope" | "evidence" | "draft" | "submission" | "external_feedback";

export type StageStatusValue = "pending" | "in_progress" | "complete" | "skipped" | "failed";

export interface StageStatus {
  status: StageStatusValue;
  updated_at?: string;
  note?: string;
  [k: string]: unknown;
}

export interface GateStatus {
  passed: boolean;
  checked_at?: string;
  not_applicable?: boolean;
  blockers?: string[];
}

export interface ProjectState {
  project_name: string;
  project_title?: string;
  funding_agency?: string | null;
  mechanism?: string | null;
  topic?: string | null;
  deadline?: string | null;
  created_at?: string;
  stages: Partial<Record<StageKey, StageStatus>>;
  gates: Partial<Record<GateName, GateStatus>>;
  settings?: Record<string, unknown>;
}

export interface MemoryCounts {
  evidence: number;
  claims: number;
  decisions: number;
  tasks: number;
  feedback: number;
  sections: number;
  gaps: number;
  anchors: number;
}

export interface PathStep {
  key: StageKey;
  label: string;
  stage: string;
  status: string;
  optional: boolean;
}

export interface NextAction {
  kind: "none" | "inbox" | "runs" | "run_stage" | "upload_then_run" | "confirm_requirements";
  stage?: string;
  flags?: Record<string, unknown>;
  force?: boolean;
  resume?: string;
  run_id?: string;
  subdir?: string;
}

export interface NextStep {
  key: string;
  title: string;
  why: string;
  action: NextAction;
  alternatives?: string[];
  requirements?: Array<{ id: string; text: string; status: string }>;
  last_run?: { id: string; status: string; error?: string | null };
  path: PathStep[];
  side: PathStep[];
}

export interface ProjectSummary {
  id: string;
  name: string;
  state: ProjectState;
  current_stage: string;
  memory: MemoryCounts;
  cost_usd: number;
  pending_inbox: number;
  next_step: NextStep;
}

export interface StageDef {
  name: string;
  state_key: StageKey | null;
  description: string;
  requires_gate: GateName | null;
  requires_stages: string[];
  interactive: boolean;
  flags: Record<string, string>;
  order: number;
  optional: boolean;
}

export type RunStatus =
  | "queued"
  | "running"
  | "waiting_for_user"
  | "completed"
  | "failed"
  | "stopped"
  | "interrupted";

export interface RunRecord {
  id: string;
  project_id: string;
  stage: string;
  status: RunStatus;
  flags: Record<string, unknown>;
  phase?: string | null;
  cost_usd: number;
  error?: string | null;
  created_at: string;
  started_at?: string | null;
  ended_at?: string | null;
  summary?: string | null;
}

export type JobStatus =
  | "pending"
  | "ready"
  | "running"
  | "waiting"
  | "completed"
  | "failed"
  | "skipped"
  | "interrupted";

export interface JobRecord {
  id: string;
  run_id: string;
  name: string;
  kind: "agent" | "session" | "code" | "inbox" | "gate" | "loop";
  contract?: string | null;
  deps: string[];
  status: JobStatus;
  attempts: number;
  result?: Record<string, unknown> | null;
  error?: string | null;
  cost_usd: number;
  started_at?: string | null;
  ended_at?: string | null;
}

export type InboxKind = "question" | "approval" | "form" | "chat";

export interface InboxOption {
  label: string;
  description?: string;
}

export interface InboxItem {
  id: string;
  project_id: string;
  run_id?: string | null;
  job_id?: string | null;
  kind: InboxKind;
  header: string;
  question: string;
  payload: {
    options?: Array<string | InboxOption>;
    multi?: boolean;
    rows?: Array<{ id: string; summary: string; [k: string]: unknown }>;
    decisions?: string[];
    schema?: Record<string, unknown>;
    example?: Record<string, unknown>;
    transcript?: string;
    [k: string]: unknown;
  };
  answer?: Record<string, unknown> | null;
  status: "pending" | "answered" | "cancelled";
  created_at: string;
  answered_at?: string | null;
}

export interface GateResult {
  gate_name: string;
  passed: boolean;
  not_applicable: boolean;
  checked_at: string;
  criteria: Array<{ criterion: string; met: boolean; notes?: string }>;
  blockers: string[];
  recommendations: string[];
}
