import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight, CalendarClock, CheckCircle2, CircleDashed, CircleDot, Compass, Inbox, Play, RotateCcw, SkipForward,
  Upload, XCircle,
} from "lucide-react";
import { useProjectStore } from "@/stores/project-store";
import { getCosts, getProject, listProjects, listRuns, setRequirement, startRun, uploadInputs } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { GateName, NextStep, PathStep, StageKey } from "@pw/shared";

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

/** Horizontal stepper: the main path with the current position, optional stages underneath. */
export function WorkflowPath({ path, side, currentStage }: { path: PathStep[]; side: PathStep[]; currentStage?: string }): React.ReactElement {
  const dot = (s: PathStep, current: boolean) => {
    const base = "flex h-7 w-7 items-center justify-center rounded-full border text-[11px] font-semibold";
    if (s.status === "complete") return <span className={`${base} border-accent bg-accent/15 text-accent`}><CheckCircle2 className="h-4 w-4" aria-hidden /></span>;
    if (s.status === "skipped") return <span className={`${base} border-border text-foreground-muted`}><SkipForward className="h-3.5 w-3.5" aria-hidden /></span>;
    if (s.status === "failed") return <span className={`${base} border-destructive text-destructive`}><XCircle className="h-4 w-4" aria-hidden /></span>;
    if (current || s.status === "in_progress") return <span className={`${base} border-accent text-accent ring-2 ring-accent/30`}><CircleDot className="h-4 w-4" aria-hidden /></span>;
    return <span className={`${base} border-border text-foreground-muted`}><CircleDashed className="h-4 w-4" aria-hidden /></span>;
  };
  return (
    <div className="space-y-2">
      <ol className="flex items-center gap-1 overflow-x-auto">
        {path.map((s, i) => {
          const current = s.stage === currentStage;
          return (
            <li key={s.key} className="flex items-center gap-1">
              <div className="flex flex-col items-center gap-1 px-1">
                {dot(s, current)}
                <span className={`text-[11px] ${current ? "font-semibold text-foreground" : "text-foreground-muted"}`}>{s.label}</span>
              </div>
              {i < path.length - 1 && <span className={`mb-4 h-px w-6 sm:w-10 ${s.status === "complete" ? "bg-accent" : "bg-border"}`} aria-hidden />}
            </li>
          );
        })}
      </ol>
      <div className="flex flex-wrap items-center gap-1 text-[11px] text-foreground-muted">
        <span className="mr-1">optional:</span>
        {side.map((s) => (
          <Badge key={s.key} variant={s.status === "complete" ? "success" : "muted"}>{s.label}</Badge>
        ))}
      </div>
    </div>
  );
}

/** The single most useful card: what to do now, with the button that does it. */
function NextStepCard({ project, step }: { project: string; step: NextStep }): React.ReactElement {
  const qc = useQueryClient();
  const nav = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["project", project] });
    qc.invalidateQueries({ queryKey: ["runs", project] });
  };
  const run = useMutation({
    mutationFn: async (opts: { stage: string; force?: boolean; resume?: string; flags?: Record<string, unknown> }) => {
      if (step.action.kind === "upload_then_run" && files.length) await uploadInputs(project, files, step.action.subdir ?? "");
      return startRun(project, opts.stage, { force: !!opts.force, resume: opts.resume, flags: opts.flags });
    },
    onSuccess: (r) => { setMessage(`Started ${r.stage} (${r.id}). Watch the Inbox badge; the run asks you there.`); invalidate(); },
    onError: (e) => setMessage(String(e)),
  });
  const confirm = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => setRequirement(project, id, status),
    onSuccess: invalidate,
    onError: (e) => setMessage(String(e)),
  });
  const a = step.action;
  const stageBtn = (label: string, opts: { force?: boolean; resume?: string; flags?: Record<string, unknown> } = {}, variant: "primary" | "secondary" = "primary") => (
    <Button variant={variant} disabled={run.isPending || (a.kind === "upload_then_run" && !files.length)} onClick={() => run.mutate({ stage: a.stage!, ...opts })}>
      {opts.resume ? <RotateCcw className="h-3.5 w-3.5" aria-hidden /> : <Play className="h-3.5 w-3.5" aria-hidden />} {label}
    </Button>
  );
  return (
    <Card className="border-accent/40">
      <CardHeader>
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-accent">
          <ArrowRight className="h-3.5 w-3.5" aria-hidden /> Next step
        </div>
        <CardTitle className="text-xl">{step.title}</CardTitle>
        <CardDescription className="text-sm">{step.why}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {a.kind === "upload_then_run" && (
          <div className="flex flex-wrap items-center gap-2">
            <input ref={fileRef} type="file" multiple className="text-xs" onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
            {stageBtn(files.length ? `Upload ${files.length} file(s) and parse the call` : "Choose the call document first")}
            <Button variant="secondary" disabled={run.isPending} onClick={() => run.mutate({ stage: a.stage! })}>
              <Upload className="h-3.5 w-3.5" aria-hidden /> Paste the text instead
            </Button>
          </div>
        )}
        {a.kind === "run_stage" && (
          <div className="flex flex-wrap items-center gap-2">
            {a.resume
              ? stageBtn(`Resume ${a.stage}`, { resume: a.resume, force: a.force })
              : stageBtn(`Run ${a.stage}${a.force ? " (force past the gate)" : ""}`, { force: a.force, flags: a.flags })}
            {a.resume && stageBtn(`Start ${a.stage} over`, { force: a.force }, "secondary")}
          </div>
        )}
        {a.kind === "confirm_requirements" && (
          <ul className="space-y-1.5">
            {(step.requirements ?? []).map((r) => (
              <li key={r.id} className="flex flex-wrap items-center gap-2 rounded border border-border px-2 py-1.5 text-sm">
                <span className="mono text-xs text-foreground-muted">{r.id}</span>
                <span className="flex-1">{r.text}</span>
                <Button size="sm" onClick={() => confirm.mutate({ id: r.id, status: "met" })}>met</Button>
                <Button size="sm" variant="secondary" onClick={() => confirm.mutate({ id: r.id, status: "not_applicable" })}>n/a</Button>
                <Button size="sm" variant="ghost" onClick={() => confirm.mutate({ id: r.id, status: "unmet" })}>unmet</Button>
              </li>
            ))}
          </ul>
        )}
        {a.kind === "inbox" && (
          <Button onClick={() => nav("/inbox")}><Inbox className="h-3.5 w-3.5" aria-hidden /> Open the Inbox</Button>
        )}
        {a.kind === "runs" && (
          <Button variant="secondary" onClick={() => nav("/runs")}>Watch the run</Button>
        )}
        {step.alternatives?.map((alt) => (
          <p key={alt} className="text-xs text-foreground-muted">{alt}</p>
        ))}
        <p className="text-xs text-foreground-muted">
          Prefer to delegate? <Link to="/pipeline" className="underline inline-flex items-center gap-1"><Compass className="h-3 w-3" aria-hidden />Ask the planner</Link> for a whole campaign, or pick any stage on the Pipeline page.
        </p>
        {message && <div className="rounded border border-border bg-surface px-2 py-1 text-xs" role="status">{message}</div>}
      </CardContent>
    </Card>
  );
}

function StartHere(): React.ReactElement {
  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: listProjects });
  return (
    <Card className="max-w-3xl">
      <CardHeader>
        <CardTitle>Start here</CardTitle>
        <CardDescription>
          {projects?.length ? "Pick a project in the switcher above, or create a new one." : "No projects yet. A proposal goes through six steps; the app tells you the next one at every point."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <ol className="grid gap-2 sm:grid-cols-3">
          {[
            ["1", "Create a project", "Name, funder, your central idea (or leave it empty and let the ideation interview develop it)."],
            ["2", "Upload the call and parse it", "The parsed call defines sections, criteria, eligibility and gates. You approve it in the Inbox."],
            ["3", "Follow the next step", "Research → draft → review → export. Each stage tells you what it needs; the Inbox is where it asks."],
          ].map(([n, title, body]) => (
            <li key={n} className="rounded border border-border p-3">
              <div className="mb-1 flex items-center gap-2"><span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent/15 text-xs font-semibold text-accent">{n}</span><span className="font-medium">{title}</span></div>
              <p className="text-xs text-foreground-muted">{body}</p>
            </li>
          ))}
        </ol>
        <Link to="/new"><Button><ArrowRight className="h-3.5 w-3.5" aria-hidden /> Create a project</Button></Link>
      </CardContent>
    </Card>
  );
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

  if (!active) return <StartHere />;
  if (error) return <div className="text-sm text-destructive">{String(error)}</div>;
  if (!project) return <div className="text-sm text-foreground-muted">Loading…</div>;

  const st = project.state;
  const step = project.next_step;
  const activeRun = runs?.find((r) => r.status === "running" || r.status === "waiting_for_user");

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>{project.name}</CardTitle>
          <CardDescription>
            {st.funding_agency ?? "—"} · {st.mechanism ?? "—"} · {st.topic ?? ""}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <WorkflowPath path={step.path} side={step.side} currentStage={step.action.stage} />
        </CardContent>
      </Card>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <NextStepCard project={active} step={step} />
        </div>
        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Now</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
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
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Gates</CardTitle>
          <CardDescription>Deterministic checks the pipeline must pass between stages. Blockers say exactly what is missing.</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
            {GATES.map((g) => {
              const gate = st.gates[g];
              return (
                <li key={g} className="rounded border border-border p-2 text-sm">
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
                  {gate?.blockers && gate.blockers.length > 0 && (
                    <ul className="mt-1 list-disc pl-4 text-xs text-foreground-muted">
                      {gate.blockers.map((b: string) => <li key={b}>{b}</li>)}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
