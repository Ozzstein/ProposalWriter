import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Play, RotateCcw, AlertTriangle } from "lucide-react";
import {
  getProject,
  launchStage,
  listSessions,
  type SessionRecord,
  type StageName,
} from "@/lib/api";
import { useProjectStore } from "@/stores/project-store";
import type { StageName as StateStageName, StageStatus } from "@pw/shared";

interface StageDef {
  slug: StageName;
  label: string;
  desc: string;
  /** matching key in ProjectState.stages */
  stateKey?: StateStageName;
  /** required free-form args prompt when launching (e.g. gate name) */
  argsPrompt?: string;
}

const STAGES: StageDef[] = [
  {
    slug: "parse-call",
    label: "Parse call",
    desc: "Extract eligibility, criteria, structure from the funding call.",
    stateKey: "call_parsing",
  },
  {
    slug: "research",
    label: "Research",
    desc: "Gather evidence, identify SOTA and gaps.",
    stateKey: "research",
  },
  {
    slug: "write-proposal",
    label: "Write proposal",
    desc: "Draft polished narrative sections.",
    stateKey: "writing",
  },
  {
    slug: "review",
    label: "Review",
    desc: "Red-team, compliance check, unsupported-claim detection.",
    stateKey: "review",
  },
  {
    slug: "external-review",
    label: "External review",
    desc: "Ingest external reviewer comments and apply patches.",
    stateKey: "external_review",
  },
  {
    slug: "gate-check",
    label: "Gate check",
    desc: "Verify a review gate (scope / evidence / draft / submission).",
    argsPrompt: "Gate name (scope | evidence | draft | submission):",
  },
  {
    slug: "pipeline-status",
    label: "Pipeline status",
    desc: "Print current progress and the next recommended action.",
  },
];

export function PipelinePage(): React.ReactElement {
  const active = useProjectStore((s) => s.activeProject);
  const qc = useQueryClient();

  const projectQ = useQuery({
    queryKey: ["project", active],
    queryFn: () => (active ? getProject(active) : Promise.resolve(null)),
    enabled: !!active,
  });

  const sessionsQ = useQuery({
    queryKey: ["sessions"],
    queryFn: listSessions,
    refetchInterval: 3000,
  });

  const launchM = useMutation({
    mutationFn: async (args: {
      stage: StageName;
      resume?: string;
      args?: string;
    }) => {
      if (!active) throw new Error("No active project");
      return launchStage(active, args.stage, {
        resume: args.resume,
        args: args.args,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sessions"] });
    },
  });

  const [confirm, setConfirm] = useState<{
    stage: StageDef;
    resumeFrom?: SessionRecord;
    argsValue: string;
  } | null>(null);

  if (!active) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pipeline control</CardTitle>
          <CardDescription>
            Pick a project in the top bar to launch stages.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const lastSessionByStage = new Map<StageName, SessionRecord>();
  for (const s of sessionsQ.data ?? []) {
    if (s.project !== active) continue;
    const existing = lastSessionByStage.get(s.stage);
    if (!existing || s.started_at > existing.started_at) {
      lastSessionByStage.set(s.stage, s);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {launchM.error && (
        <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <div>{String(launchM.error)}</div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {STAGES.map((stage) => {
          const stageState =
            stage.stateKey && projectQ.data?.state.stages[stage.stateKey];
          const lastSession = lastSessionByStage.get(stage.slug);
          return (
            <StageCard
              key={stage.slug}
              stage={stage}
              stageState={stageState}
              lastSession={lastSession}
              onRun={() =>
                setConfirm({ stage, argsValue: "" })
              }
              onResume={() =>
                setConfirm({
                  stage,
                  resumeFrom: lastSession,
                  argsValue: lastSession?.args ?? "",
                })
              }
              disabled={launchM.isPending}
            />
          );
        })}
      </div>

      {confirm && (
        <ConfirmLaunch
          project={active}
          stage={confirm.stage}
          resumeFrom={confirm.resumeFrom}
          argsValue={confirm.argsValue}
          pending={launchM.isPending}
          onCancel={() => setConfirm(null)}
          onConfirm={(argsValue) => {
            launchM.mutate({
              stage: confirm.stage.slug,
              resume: confirm.resumeFrom?.sdk_session_id,
              args: argsValue || undefined,
            });
            setConfirm(null);
          }}
        />
      )}
    </div>
  );
}

function StageCard({
  stage,
  stageState,
  lastSession,
  onRun,
  onResume,
  disabled,
}: {
  stage: StageDef;
  stageState?: StageStatus | false;
  lastSession?: SessionRecord;
  onRun: () => void;
  onResume: () => void;
  disabled: boolean;
}): React.ReactElement {
  const status = stageState ? stageState.status : null;
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{stage.label}</CardTitle>
          {status && <StatusBadge status={status} />}
        </div>
        <CardDescription>{stage.desc}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 text-xs">
        {lastSession && (
          <div className="rounded-md border border-border bg-background/50 p-2">
            <div className="flex items-center justify-between gap-2">
              <span className="text-foreground-muted">Last session</span>
              <SessionStatusBadge status={lastSession.status} />
            </div>
            <div className="mono mt-1 text-[11px] text-foreground-muted">
              {lastSession.started_at.replace("T", " ").slice(0, 19)}
            </div>
            {lastSession.error && (
              <div className="mt-1 text-destructive">{lastSession.error}</div>
            )}
          </div>
        )}
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={onRun}
            disabled={disabled}
            className="gap-1"
          >
            <Play className="h-3.5 w-3.5" aria-hidden />
            Run
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={onResume}
            disabled={disabled || !lastSession?.sdk_session_id}
            className="gap-1"
            aria-label={`Resume ${stage.label}`}
            title={
              lastSession?.sdk_session_id
                ? "Resume the last SDK session"
                : "No resumable session"
            }
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden />
            Resume
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function StatusBadge({
  status,
}: {
  status: StageStatus["status"];
}): React.ReactElement {
  const map = {
    pending: { variant: "muted" as const, label: "pending" },
    in_progress: { variant: "warning" as const, label: "in progress" },
    complete: { variant: "success" as const, label: "complete" },
    failed: { variant: "destructive" as const, label: "failed" },
  };
  const m = map[status] ?? map.pending;
  return <Badge variant={m.variant}>{m.label}</Badge>;
}

function SessionStatusBadge({
  status,
}: {
  status: SessionRecord["status"];
}): React.ReactElement {
  const map = {
    running: { variant: "warning" as const, label: "running" },
    completed: { variant: "success" as const, label: "completed" },
    failed: { variant: "destructive" as const, label: "failed" },
    stopped: { variant: "muted" as const, label: "stopped" },
  };
  const m = map[status];
  return <Badge variant={m.variant}>{m.label}</Badge>;
}

function ConfirmLaunch({
  project,
  stage,
  resumeFrom,
  argsValue: initialArgs,
  pending,
  onCancel,
  onConfirm,
}: {
  project: string;
  stage: StageDef;
  resumeFrom?: SessionRecord;
  argsValue: string;
  pending: boolean;
  onCancel: () => void;
  onConfirm: (argsValue: string) => void;
}): React.ReactElement {
  const [args, setArgs] = useState(initialArgs);
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="launch-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/70 p-4"
    >
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle id="launch-title">
            {resumeFrom ? "Resume" : "Run"} /{stage.slug}
          </CardTitle>
          <CardDescription>
            Project: <span className="mono">{project}</span>
            {resumeFrom?.sdk_session_id && (
              <>
                {" · "}Resuming session{" "}
                <span className="mono">
                  {resumeFrom.sdk_session_id.slice(0, 8)}…
                </span>
              </>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {stage.argsPrompt && (
            <label className="flex flex-col gap-1 text-xs text-foreground-muted">
              {stage.argsPrompt}
              <input
                type="text"
                value={args}
                onChange={(e) => setArgs(e.target.value)}
                className="h-8 rounded-md border border-border bg-background px-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                autoFocus
              />
            </label>
          )}
          <div className="rounded-md border border-border bg-background p-2 text-[11px] text-foreground-muted">
            The SDK will run this slash command against{" "}
            <span className="mono">runs/{project}/</span>. Live progress appears
            on the Activity page and pulses matching nodes on the System graph.
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onCancel} disabled={pending}>
              Cancel
            </Button>
            <Button
              onClick={() => onConfirm(args)}
              disabled={pending || (!!stage.argsPrompt && !args.trim())}
            >
              {pending
                ? "Launching…"
                : resumeFrom
                  ? "Resume"
                  : "Run stage"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
