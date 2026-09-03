import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Pause, Play, Trash2 } from "lucide-react";
import { cn } from "@/lib/cn";
import { useEventStore } from "@/stores/event-store";
import { eventFamily, type EventFamily, type PipelineEvent } from "@pw/shared";

type HookKind = EventFamily | "other";

const HOOK_FILTERS: Array<{ value: HookKind | "all"; label: string }> = [
  { value: "all", label: "All" },
  { value: "stage", label: "Stages" },
  { value: "job", label: "Jobs" },
  { value: "agent", label: "Agents" },
  { value: "tool", label: "Tools" },
  { value: "inbox", label: "Inbox" },
  { value: "gate", label: "Gates" },
  { value: "graph", label: "Graph" },
  { value: "cost", label: "Cost" },
];

const HOOK_COLOR: Record<HookKind, string> = {
  stage: "bg-info/20 text-info",
  job: "bg-info/20 text-info",
  agent: "bg-warning/20 text-warning",
  tool: "bg-accent/20 text-accent",
  inbox: "bg-destructive/20 text-destructive",
  gate: "bg-warning/20 text-warning",
  graph: "bg-muted text-foreground-muted",
  cost: "bg-muted text-foreground-muted",
  project: "bg-muted text-foreground-muted",
  other: "bg-muted text-foreground-muted",
};

export function ActivityPage(): React.ReactElement {
  const events = useEventStore((s) => s.events);
  const paused = useEventStore((s) => s.paused);
  const setPaused = useEventStore((s) => s.setPaused);
  const clear = useEventStore((s) => s.clear);
  const status = useEventStore((s) => s.status);

  const [hookFilter, setHookFilter] = useState<HookKind | "all">("all");
  const [toolFilter, setToolFilter] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);

  const filtered = useMemo(() => {
    return events
      .slice()
      .reverse()
      .filter((e) => (hookFilter === "all" ? true : eventFamily(e.kind) === hookFilter))
      .filter((e) =>
        toolFilter.trim()
          ? (e.tool_name ?? "").toLowerCase().includes(toolFilter.trim().toLowerCase())
          : true,
      );
  }, [events, hookFilter, toolFilter]);

  const ratePerMin = useMemo(() => {
    const now = Date.now();
    const cutoff = now - 60_000;
    let n = 0;
    for (let i = events.length - 1; i >= 0; i--) {
      const t = Date.parse(events[i].ts);
      if (Number.isFinite(t) && t >= cutoff) n++;
      else break;
    }
    return n;
  }, [events]);

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard label="Events buffered" value={String(events.length)} />
        <StatCard label="Events / minute" value={String(ratePerMin)} accent />
        <StatCard
          label="Stream status"
          value={status[0].toUpperCase() + status.slice(1)}
        />
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0 pb-3">
          <CardTitle>Live activity</CardTitle>
          <div className="flex items-center gap-2">
            <input
              type="search"
              value={toolFilter}
              onChange={(e) => setToolFilter(e.target.value)}
              placeholder="Filter by tool…"
              className="h-8 w-48 rounded-md border border-border bg-background px-2 text-xs text-foreground placeholder:text-foreground-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Filter by tool name"
            />
            <div
              role="tablist"
              aria-label="Hook type filter"
              className="flex gap-1 rounded-md border border-border bg-background p-0.5"
            >
              {HOOK_FILTERS.map((f) => (
                <button
                  key={f.value}
                  role="tab"
                  aria-selected={hookFilter === f.value}
                  onClick={() => setHookFilter(f.value)}
                  className={cn(
                    "rounded px-2 py-1 text-[11px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    hookFilter === f.value
                      ? "bg-muted text-foreground"
                      : "text-foreground-muted hover:text-foreground",
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => setPaused(!paused)}
              aria-label={paused ? "Resume feed" : "Pause feed"}
              className="flex h-8 items-center gap-1 rounded-md border border-border bg-background px-2 text-xs text-foreground-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {paused ? (
                <Play className="h-3.5 w-3.5" aria-hidden />
              ) : (
                <Pause className="h-3.5 w-3.5" aria-hidden />
              )}
              {paused ? "Resume" : "Pause"}
            </button>
            <button
              onClick={() => clear()}
              aria-label="Clear feed"
              className="flex h-8 items-center gap-1 rounded-md border border-border bg-background px-2 text-xs text-foreground-muted hover:text-destructive focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden />
              Clear
            </button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-auto p-0">
          {filtered.length === 0 ? (
            <div className="p-6 text-sm text-foreground-muted">
              No events yet. Run a slash command in Claude Code or watch as
              agents spawn — rows stream in as hooks fire.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {filtered.map((e, idx) => (
                <EventRow
                  key={`${e.ts}-${idx}`}
                  event={e}
                  expanded={expanded === idx}
                  onToggle={() => setExpanded(expanded === idx ? null : idx)}
                />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}): React.ReactElement {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1 py-4">
        <span className="text-[11px] uppercase tracking-wide text-foreground-muted">
          {label}
        </span>
        <span
          className={cn(
            "mono text-2xl font-semibold tabular-nums",
            accent && "text-accent",
          )}
        >
          {value}
        </span>
      </CardContent>
    </Card>
  );
}

function EventRow({
  event,
  expanded,
  onToggle,
}: {
  event: PipelineEvent;
  expanded: boolean;
  onToggle: () => void;
}): React.ReactElement {
  const time = event.ts.slice(11, 23);
  return (
    <li>
      <button
        onClick={onToggle}
        className="flex w-full items-start gap-3 px-4 py-2 text-left text-xs hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <span className="mono w-24 shrink-0 tabular-nums text-foreground-muted">
          {time}
        </span>
        <span
          className={cn(
            "inline-flex h-5 shrink-0 items-center rounded px-1.5 text-[10px] font-medium",
            HOOK_COLOR[eventFamily(event.kind)],
          )}
        >
          {event.kind}
        </span>
        <span className="mono w-28 shrink-0 truncate text-foreground">
          {event.tool_name ?? "—"}
        </span>
        <span className="flex-1 truncate text-foreground-muted">
          {event.agent ? `${event.agent} · ` : ""}
          {summarizeInput(event.data)}
        </span>
        {typeof event.data.duration_ms === "number" && (
          <span className="mono shrink-0 tabular-nums text-foreground-muted">
            {event.data.duration_ms}ms
          </span>
        )}
      </button>
      {expanded && (
        <pre className="mono overflow-x-auto bg-background px-4 py-3 text-[11px] text-foreground-muted">
          {JSON.stringify(event, null, 2)}
        </pre>
      )}
    </li>
  );
}

function summarizeInput(input?: Record<string, unknown>): string {
  if (!input) return "";
  const keys = Object.keys(input).slice(0, 4);
  return keys
    .map((k) => {
      const v = input[k];
      const s = typeof v === "string" ? v : JSON.stringify(v);
      const trimmed = s.length > 40 ? s.slice(0, 40) + "…" : s;
      return `${k}=${trimmed}`;
    })
    .join("  ");
}
