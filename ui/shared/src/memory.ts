export type MemoryStore =
  | "evidence"
  | "claims"
  | "decisions"
  | "tasks"
  | "feedback"
  | "overrides";

export interface EvidenceRecord {
  source_id: string;
  title?: string;
  authors?: string;
  year?: number;
  type?: string;
  quality?: string;
  tags?: string[];
  extract?: string;
  url?: string;
  [k: string]: unknown;
}

export interface ClaimRecord {
  claim_id: string;
  text?: string;
  source_ids?: string[];
  confidence?: number;
  status?: string;
  category?: string;
  [k: string]: unknown;
}

export interface DecisionRecord {
  decision_id: string;
  timestamp?: string;
  agent?: string;
  decision?: string;
  rationale?: string;
  [k: string]: unknown;
}

export interface TaskRecord {
  task_id: string;
  dedupe_key?: string;
  status?: string;
  agent?: string;
  started_at?: string;
  completed_at?: string;
  [k: string]: unknown;
}

export interface FeedbackRecord {
  feedback_id: string;
  round?: number;
  comment?: string;
  status?: string;
  assignee?: string;
  resolution?: string;
  [k: string]: unknown;
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

export type AnyMemoryRecord =
  | EvidenceRecord
  | ClaimRecord
  | DecisionRecord
  | TaskRecord
  | FeedbackRecord
  | OverrideRecord;
