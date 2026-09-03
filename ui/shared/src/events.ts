/** One line of the agency event log (also the SSE payload). */
export interface PipelineEvent {
  seq?: number;
  /** ISO 8601 UTC timestamp */
  ts: string;
  project_id?: string | null;
  run_id?: string | null;
  job_id?: string | null;
  /** e.g. stage:start, job:done, agent:start, tool:start, inbox:pending, gate:result, cost */
  kind: string;
  /** contract name of the agent that produced the event, if any */
  agent?: string | null;
  tool_name?: string | null;
  data: Record<string, unknown>;
}

export const EVENT_FAMILIES = ["stage", "job", "agent", "tool", "inbox", "gate", "graph", "cost", "project"] as const;
export type EventFamily = (typeof EVENT_FAMILIES)[number];

export function eventFamily(kind: string): EventFamily | "other" {
  const head = kind.split(":")[0] as EventFamily;
  return (EVENT_FAMILIES as readonly string[]).includes(head) ? head : "other";
}
