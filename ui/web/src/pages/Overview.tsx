import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { CalendarClock, CheckCircle2, CircleDashed, CircleDot, Inbox, SkipForward, XCircle } from "lucide-react";
import { useProjectStore } from "@/stores/project-store";
import { getCosts, getProject, listRuns } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { GateName, StageKey } from "@pw/shared";

export const STAGE_KEYS: Array<{ key: StageKey; label: string; optional?: boolean }> = [
  { key: "ideation", label: "Ideation", optional: true },
  { key: "call_parsing", label: "Call parsing" },
  { key: "research", label: "Research" },
  { key: "writing", label: "Writing" },
  { key: "finance", label: "Finance", optional: true },
  { key: "figures", label: "Figures", optional: true },
  { key: "business_plan", label: "Business plan", optional: true },
  { key: "review", label: "Review" },
  { key: "external_review", label: "External review", optional: true },
  { key: "export", label: "Export" },
];

export const GATES: GateName[] = ["scope", "evidence", "draft", "submission", "external_feedback"];

export function StageBadge({ status }: { status?: string }): React.ReactElement {
  if (status === "complete") return <Badge variant="success"><CheckCircle2 className="h-3 w-3" aria-hidden />complete</Badge>;
  if (status === "in_progress") return <Badge variant="info"><CircleDot className="h-3 w-3" aria-hidden />in progress</Badge>;
  if (status === "failed") return <Badge variant="destructive"><XCircle className="h-3 w-3" aria-hidden />failed</Badge>;
  if (status === "skipped") return <Badge variant="muted"><SkipForward className="h-3 w-3" aria-hidden />skipped</Badge>;
  return <Badge variant="muted"><CircleDashed className="h-3 w-3" aria-hidden />pending</Badge>;
}

export function OverviewPage(): React.ReactElement {
  const active = useProjectStore((s) => s.activeProject);
  const { data: project, error } = useQuery({
    queryKey: ["project", active],
    queryFn: () => getProject(active!),
    enabled: !!active,
    refetchInterval: 5000,
  });
  const { data: runs } = useQuery({ queryKey: ["runs", active], queryFn: () => listRuns(active!), enabled: !!active, refetchInterval: 5000 });
  const { data: costs } = useQuery({ queryKey: ["costs", active], queryFn: () => getCosts(active!), enabled: !!active, refetchInterval: 10000 });

  if (!active) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No project selected</CardTitle>
          <CardDescription>
            Pick a project in the sidebar or <Link className="underline" to="/new">create one</Link>.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }
  if (error) return <div className="text-sm text-destructive">{String(error)}</div>;
  if (!project) return <div className="text-sm text-foreground-muted">Loading…</div>;

  const st = project.state;
  const activeRun = runs?.find((r) => r.status === "running" || r.status === "waiting_for_user");

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>{project.name}</CardTitle>
          <CardDescription>
            {st.funding_agency ?? "—"} · {st.mechanism ?? "—"} · {st.topic ?? ""}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          <div>
            <h3 className="mb-2 text-xs uppercase tracking-wide text-foreground-muted">Stages</h3>
            <ul className="space-y-1.5">
              {STAGE_KEYS.map((s) => (
                <li key={s.key} className="flex items-center justify-between text-sm">
                  <span className={s.optional ? "text-foreground-muted" : ""}>{s.label}</span>
                  <StageBadge status={st.stages[s.key]?.status} />
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="mb-2 text-xs uppercase tracking-wide text-foreground-muted">Gates</h3>
            <ul className="space-y-1.5">
              {GATES.map((g) => {
                const gate = st.gates[g];
                return (
                  <li key={g} className="flex flex-col gap-0.5 text-sm">
                    <div className="flex items-center justify-between">
                      <span>{g.replace("_", " ")}</span>
                      {gate?.not_applicable ? (
                        <Badge variant="muted">n/a</Badge>
                      ) : gate?.passed ? (
                        <Badge variant="success">passed</Badge>
                      ) : gate?.checked_at ? (
                        <Badge variant="destructive">failed</Badge>
                      ) : (
                        <Badge variant="muted">unchecked</Badge>
                      )}
                    </div>
                    {gate?.blockers && gate.blockers.length > 0 && !gate.passed && (
                      <ul className="ml-2 list-disc text-[11px] text-foreground-muted">
                        {gate.blockers.slice(0, 3).map((b) => (
                          <li key={b}>{b}</li>
                        ))}
                      </ul>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        </CardContent>
      </Card>
      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Now</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">Current stage</span>
              <span className="mono">{project.current_stage}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">Active run</span>
              <span className="mono">{activeRun ? `${activeRun.stage} · ${activeRun.status}` : "none"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">Pending questions</span>
              <Link to="/inbox" className="flex items-center gap-1 underline">
                <Inbox className="h-3 w-3" aria-hidden /> {project.pending_inbox}
              </Link>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-foreground-muted">Spend</span>
              <span className="mono">${(costs?.total_usd ?? project.cost_usd).toFixed(2)}</span>
            </div>
            {st.deadline && (
              <div className="flex items-center justify-between">
                <span className="text-foreground-muted">Deadline</span>
                <span className="mono flex items-center gap-1"><CalendarClock className="h-3 w-3" aria-hidden />{st.deadline}</span>
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Graph</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-2 text-sm">
            {(
              [
                ["sources", project.memory.evidence],
                ["claims", project.memory.claims],
                ["gaps", project.memory.gaps],
                ["anchors", project.memory.anchors],
                ["sections", project.memory.sections],
                ["decisions", project.memory.decisions],
                ["feedback", project.memory.feedback],
                ["runs", project.memory.tasks],
              ] as Array<[string, number]>
            ).map(([label, n]) => (
              <div key={label} className="flex items-center justify-between rounded border border-border px-2 py-1">
                <span className="text-foreground-muted">{label}</span>
                <span className="mono">{n}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
