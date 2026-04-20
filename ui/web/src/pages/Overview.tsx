import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  CircleDashed,
  CircleDot,
  XCircle,
} from "lucide-react";
import { useProjectStore } from "@/stores/project-store";
import { getProject } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { GateName, StageName } from "@pw/shared";

const STAGES: StageName[] = [
  "call_parsing",
  "research",
  "writing",
  "review",
  "template_population",
];

const GATES: GateName[] = ["scope", "evidence", "draft", "submission"];

function StageBadge({ status }: { status?: string }): React.ReactElement {
  if (status === "complete") {
    return (
      <Badge variant="success">
        <CheckCircle2 className="h-3 w-3" aria-hidden />
        complete
      </Badge>
    );
  }
  if (status === "in_progress") {
    return (
      <Badge variant="info">
        <CircleDot className="h-3 w-3" aria-hidden />
        in progress
      </Badge>
    );
  }
  if (status === "failed") {
    return (
      <Badge variant="destructive">
        <XCircle className="h-3 w-3" aria-hidden />
        failed
      </Badge>
    );
  }
  return (
    <Badge variant="muted">
      <CircleDashed className="h-3 w-3" aria-hidden />
      pending
    </Badge>
  );
}

function GateBadge({
  passed,
  checked,
}: {
  passed?: boolean;
  checked?: string;
}): React.ReactElement {
  if (passed === true) {
    return (
      <Badge variant="success">
        <CheckCircle2 className="h-3 w-3" aria-hidden />
        passed {checked ? `· ${checked.slice(0, 10)}` : ""}
      </Badge>
    );
  }
  if (passed === false) {
    return (
      <Badge variant="warning">
        <AlertCircle className="h-3 w-3" aria-hidden />
        not passed
      </Badge>
    );
  }
  return (
    <Badge variant="muted">
      <CircleDashed className="h-3 w-3" aria-hidden />
      unchecked
    </Badge>
  );
}

function formatStage(name: StageName): string {
  return name.replace(/_/g, " ");
}

function daysUntil(iso?: string): { days: number; isPast: boolean } | null {
  if (!iso) return null;
  const then = new Date(iso).getTime();
  const now = Date.now();
  if (Number.isNaN(then)) return null;
  const diffMs = then - now;
  const days = Math.ceil(diffMs / 86_400_000);
  return { days: Math.abs(days), isPast: diffMs < 0 };
}

export function OverviewPage(): React.ReactElement {
  const project = useProjectStore((s) => s.activeProject);

  const { data, isLoading, error } = useQuery({
    queryKey: ["project", project],
    queryFn: () => getProject(project!),
    enabled: Boolean(project),
    refetchInterval: 10_000,
  });

  if (!project) {
    return (
      <EmptyState
        title="No project selected"
        description="Pick a project from the switcher above. If the list is empty, run /start-proposal in Claude Code to create one."
      />
    );
  }
  if (isLoading) return <Skeleton />;
  if (error || !data) {
    return (
      <EmptyState
        title="Could not load project"
        description={String(error ?? "")}
      />
    );
  }

  const { state, memory } = data;
  const countdown = daysUntil(state.deadline);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">
          {state.project_title ?? state.project_name}
        </h1>
        <div className="flex flex-wrap items-center gap-3 text-xs text-foreground-muted">
          {state.funding_agency && <span>{state.funding_agency}</span>}
          {state.mechanism && (
            <span className="mono">{state.mechanism}</span>
          )}
          {state.applicant && <span>· {state.applicant}</span>}
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <KpiCard label="Sources" value={memory.evidence} />
        <KpiCard label="Claims" value={memory.claims} />
        <KpiCard label="Decisions" value={memory.decisions} />
        <KpiCard
          label="Deadline"
          value={
            countdown
              ? countdown.isPast
                ? `${countdown.days}d past`
                : `${countdown.days}d left`
              : "—"
          }
          hint={state.deadline?.slice(0, 10)}
          tone={
            countdown?.isPast
              ? "destructive"
              : countdown && countdown.days <= 7
                ? "warning"
                : "default"
          }
          icon={<CalendarClock className="h-4 w-4" aria-hidden />}
        />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pipeline stages</CardTitle>
            <CardDescription>
              Status of each orchestrator run for this project.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border">
              {STAGES.map((name) => {
                const stage = state.stages[name];
                return (
                  <li
                    key={name}
                    className="flex items-center justify-between gap-3 py-2.5"
                  >
                    <span className="text-sm capitalize">
                      {formatStage(name)}
                    </span>
                    <div className="flex items-center gap-3">
                      {stage?.completed_at && (
                        <span className="mono text-[11px] text-foreground-muted">
                          {stage.completed_at.slice(0, 10)}
                        </span>
                      )}
                      <StageBadge status={stage?.status} />
                    </div>
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Review gates</CardTitle>
            <CardDescription>
              Each gate must pass before the next stage advances.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border">
              {GATES.map((name) => {
                const gate = state.gates[name];
                return (
                  <li
                    key={name}
                    className="flex items-center justify-between gap-3 py-2.5"
                  >
                    <span className="text-sm capitalize">{name}</span>
                    <GateBadge passed={gate?.passed} checked={gate?.checked_at} />
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function KpiCard({
  label,
  value,
  hint,
  tone = "default",
  icon,
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "warning" | "destructive";
  icon?: React.ReactNode;
}): React.ReactElement {
  const toneCls =
    tone === "destructive"
      ? "text-destructive"
      : tone === "warning"
        ? "text-warning"
        : "text-foreground";
  return (
    <Card>
      <CardContent className="flex flex-col gap-1">
        <div className="flex items-center justify-between text-xs uppercase tracking-wide text-foreground-muted">
          <span>{label}</span>
          {icon}
        </div>
        <span className={`mono text-2xl font-semibold ${toneCls}`}>
          {value}
        </span>
        {hint && (
          <span className="mono text-[11px] text-foreground-muted">{hint}</span>
        )}
      </CardContent>
    </Card>
  );
}

function Skeleton(): React.ReactElement {
  return (
    <div className="flex flex-col gap-4">
      <div className="h-7 w-72 rounded bg-muted" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 rounded-lg bg-muted" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="h-64 rounded-lg bg-muted" />
        <div className="h-64 rounded-lg bg-muted" />
      </div>
    </div>
  );
}

function EmptyState({
  title,
  description,
}: {
  title: string;
  description?: string;
}): React.ReactElement {
  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-2 py-8">
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardContent>
    </Card>
  );
}
