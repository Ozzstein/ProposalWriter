export type HookKind =
  | "SessionStart"
  | "UserPromptSubmit"
  | "PreToolUse"
  | "PostToolUse"
  | "Stop"
  | "SdkStream";

export interface PipelineEvent {
  /** ISO 8601 UTC timestamp */
  ts: string;
  /** Monotonic per-emission id; useful for SSE resume */
  seq?: number;
  session_id: string;
  hook: HookKind;
  tool_name?: string;
  tool_use_id?: string;
  tool_input_summary?: Record<string, unknown>;
  tool_output_summary?: Record<string, unknown>;
  duration_ms?: number;
  /** Best-effort inference of runs/<name>/ from tool inputs/outputs */
  project_hint?: string;
  /** When tool_name=="Agent"/"Task", which agents/ file the prompt referenced */
  agent_hint?: string;
  cwd?: string;
  /** Free-form extra payload (kept small; never full file contents) */
  extra?: Record<string, unknown>;
}
