import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, ArrowRight, Compass, Lock, Play, RotateCcw, ShieldCheck } from "lucide-react";
import { getPlan, getProject, listRuns, listStages, runGate, startPlan, startRun } from "@/lib/api";
import { useProjectStore } from "@/stores/project-store";
import type { StageDef, StageKey } from "@pw/shared";
import { StageBadge } from "./Overview";

export function PipelinePage(): React.ReactElement {
  const active = useProjectStore((s) => s.activeProject);
  const qc = useQueryClient();
  const { data: stages } = useQuery({ queryKey: ["stages"], queryFn: listStages });
  const { data: project } = useQuery({ queryKey: ["project", active], queryFn: () => getProject(active!), enabled: !!active, refetchInterval: 4000 });
  const { data: runs } = useQuery({ queryKey: ["runs", active], queryFn: () => listRuns(active!), enabled: !!active, refetchInterval: 4000 });
  const [flags, setFlags] = useState<Record<string, Record<string, string>>>({});
  const [force, setForce] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [goal, setGoal] = useState("");
  const { data: plan } = useQuery({ queryKey: ["plan", active], queryFn: () => getPlan(active!), enabled: !!active, refetchInterval: 4000 });
  const planStart = useMutation({
    mutationFn: () => startPlan(active!, { goal }),
    onSuccess: (run) => {
      setMessage(`Planning started (${run.id}); approve the plan in the inbox`);
      qc.invalidateQueries({ queryKey: ["runs", active] });
      qc.invalidateQueries({ queryKey: ["plan", active] });
    },
    onError: (e) => setMessage(String(e)),
  });

  const start = useMutation({
    mutationFn: ({ stage, resume }: { stage: string; resume?: string }) =>
      startRun(active!, stage, {
        flags: Object.fromEntries(Object.entries(flags[stage] ?? {}).filter(([, v]) => v !== "")),
        resume,
        force: !!force[stage],
      }),
    onSuccess: (run) => {
      setMessage(`Started ${run.stage} (${run.id})`);
      qc.invalidateQueries({ queryKey: ["runs", active] });
    },
    onError: (e) => setMessage(String(e)),
  });
  const gate = useMutation({
    mutationFn: (g: string) => runGate(active!, g),
    onSuccess: (res) => {
      setMessage(`Gate ${res.gate_name}: ${res.not_applicable ? "not applicable" : res.passed ? "PASS" : "FAIL — " + res.blockers.join("; ")}`);
      qc.invalidateQueries({ queryKey: ["project", active] });
    },
    onError: (e) => setMessage(String(e)),
  });

  if (!active) return <div className="text-sm text-foreground-muted">Select a project first.</div>;
  const activeRun = runs?.find((r) => r.status === "running" || r.status === "waiting_for_user");

  return (
    <div className="space-y-4">
      {message && (
        <div className="rounded border border-border bg-surface px-3 py-2 text-xs text-foreground-muted" role="status">
          {message}
        </div>
      )}
      {activeRun && (
        <div className="flex items-center gap-2 rounded border border-warning/40 bg-warning/10 px-3 py-2 text-xs">
          <AlertTriangle className="h-3 w-3 text-warning" aria-hidden />
          Run <span className="mono">{activeRun.id}</span> ({activeRun.stage}) is {activeRun.status.replace("_", " ")}
          {activeRun.status === "waiting_for_user" && (
            <Link to="/inbox" className="underline">answer in the inbox</Link>
          )}
          {" · "}
          <Link to="/runs" className="underline">details</Link>
        </div>
      )}
      <div className="rounded border border-border bg-surface px-3 py-2 text-xs text-foreground-muted">
        Stages run in order: <span className="mono">parse-call → ideate → research → write-proposal → review → export</span>, with finance, figures,
        business-plan and external-feedback as side steps governed by the project scope (excluded stages need force). Locked stages say what they wait for.
        The recommended next stage is highlighted; the <Link to="/" className="underline">Overview</Link> explains it.
      </div>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Compass className="h-4 w-4 text-accent" aria-hidden />
            <CardTitle className="text-base">Planner</CardTitle>
          </div>
          <CardDescription>
            Describe what you want next. The planning agent proposes a campaign of stage runs, you approve it in the inbox, the engine executes it and re-plans once if a step stops.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <input
              className="h-8 flex-1 rounded border border-border bg-background px-2 text-sm"
              placeholder="e.g. get the draft gate passed with a focus on the impact section"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
            />
            <Button size="sm" disabled={!!activeRun || planStart.isPending || goal.trim().length < 3} onClick={() => planStart.mutate()}>
              <Compass className="h-3 w-3" aria-hidden /> Plan
            </Button>
          </div>
          {plan && (
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-medium">Latest plan</span>
                <Badge variant={plan.status === "completed" ? "success" : plan.status === "stopped" ? "warning" : "muted"}>{plan.status}</Badge>
                {plan.campaign_active && <span className="text-foreground-muted">campaign running</span>}
                <span className="ml-auto text-foreground-muted">{plan.goal}</span>
              </div>
              <p className="text-foreground-muted">{plan.assessment}</p>
              {plan.questions_for_researcher.length > 0 && (
                <ul className="list-disc pl-4 text-foreground-muted">
                  {plan.questions_for_researcher.map((q) => <li key={q}>{q}</li>)}
                </ul>
              )}
              <table className="w-full text-left">
                <thead className="text-foreground-muted">
                  <tr><th className="pr-2">#</th><th className="pr-2">stage</th><th className="pr-2">flags</th><th className="pr-2">status</th><th>rationale</th></tr>
                </thead>
                <tbody>
                  {plan.steps.map((st) => (
                    <tr key={st.step} className="border-t border-border align-top">
                      <td className="pr-2 py-1">{st.step}</td>
                      <td className="pr-2 py-1 mono">{st.stage}{st.force ? " (force)" : ""}</td>
                      <td className="pr-2 py-1 mono">{Object.entries(st.flags).map(([k, v]) => `${k}=${String(v)}`).join(" ") || "–"}</td>
                      <td className="pr-2 py-1">
                        <Badge variant={st.status === "completed" ? "success" : st.status === "failed" || st.status === "blocked" ? "warning" : "muted"}>{st.status}</Badge>
                        {st.run_id && <Link to="/runs" className="ml-1 underline">run</Link>}
                      </td>
                      <td className="py-1 text-foreground-muted">{st.rationale}{st.error ? ` — ${st.error}` : ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {plan.error && <p className="text-warning">{plan.error}</p>}
            </div>
          )}
        </CardContent>
      </Card>
      <div className="grid gap-3 md:grid-cols-2">
        {(stages ?? []).filter((s: StageDef) => s.name !== "plan").map((s: StageDef, idx: number) => {
          const last = runs?.find((r) => r.stage === s.name);
          const stateStatus = s.state_key ? project?.state.stages[s.state_key]?.status : undefined;
          const gateOk = s.requires_gate ? project?.state.gates[s.requires_gate]?.passed : true;
          const missing = s.requires_stages.filter((k) => !["complete", "skipped"].includes(project?.state.stages[k as StageKey]?.status ?? ""));
          const isNext = project?.next_step.action.stage === s.name;
          const locked = missing.length > 0 || (s.requires_gate && gateOk === false && !force[s.name]);
          return (
            <Card key={s.name} className={isNext ? "border-accent/60 ring-1 ring-accent/30" : locked ? "opacity-80" : ""}>
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-surface text-[11px] text-foreground-muted">{idx + 1}</span>
                    {s.name}
                    {s.optional && <Badge variant="muted">optional</Badge>}
                    {isNext && <Badge variant="success"><ArrowRight className="h-3 w-3" aria-hidden />next</Badge>}
                  </CardTitle>
                  <StageBadge status={stateStatus} />
                </div>
                <CardDescription>{s.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {missing.length > 0 && (
                  <div className="flex items-center gap-2 text-xs text-foreground-muted">
                    <Lock className="h-3 w-3" aria-hidden /> waits for {missing.join(", ")} to complete
                  </div>
                )}
                {s.requires_gate && (
                  <div className="flex items-center gap-2 text-xs">
                    <ShieldCheck className={`h-3 w-3 ${gateOk ? "text-accent" : "text-warning"}`} aria-hidden />
                    requires gate <span className="mono">{s.requires_gate}</span>
                    <Badge variant={gateOk ? "success" : "warning"}>{gateOk ? "passed" : "not passed"}</Badge>
                    <Button size="sm" variant="ghost" onClick={() => gate.mutate(s.requires_gate!)}>re-check</Button>
                    <label className="ml-auto flex items-center gap-1">
                      <input type="checkbox" checked={!!force[s.name]} onChange={(e) => setForce({ ...force, [s.name]: e.target.checked })} />
                      force
                    </label>
                  </div>
                )}
                {Object.keys(s.flags).length > 0 && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-foreground-muted">flags</summary>
                    <div className="mt-1 grid gap-1">
                      {Object.entries(s.flags).map(([k, help]) => (
                        <label key={k} className="grid grid-cols-[8rem_1fr] items-center gap-2">
                          <span className="mono" title={help}>{k}</span>
                          <input
                            className="h-7 rounded border border-border bg-background px-2"
                            placeholder={help}
                            value={flags[s.name]?.[k] ?? ""}
                            onChange={(e) => setFlags({ ...flags, [s.name]: { ...(flags[s.name] ?? {}), [k]: e.target.value } })}
                          />
                        </label>
                      ))}
                    </div>
                  </details>
                )}
                <div className="flex items-center gap-2">
                  <Button size="sm" disabled={!!activeRun || start.isPending || !!locked} title={locked ? "prerequisites not met (tick force to override a gate)" : undefined} onClick={() => start.mutate({ stage: s.name })}>
                    <Play className="h-3 w-3" aria-hidden /> Run
                  </Button>
                  {last && last.status !== "completed" && (
                    <Button size="sm" variant="secondary" disabled={!!activeRun} onClick={() => start.mutate({ stage: s.name, resume: last.id })}>
                      <RotateCcw className="h-3 w-3" aria-hidden /> Resume
                    </Button>
                  )}
                  {last && (
                    <span className="ml-auto text-[11px] text-foreground-muted">
                      last: {last.status} · ${last.cost_usd.toFixed(2)}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Gates</CardTitle>
          <CardDescription>Deterministic checks over the proposal graph. Thresholds come from the funder pack.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {["scope", "evidence", "draft", "submission", "external_feedback"].map((g) => (
            <Button key={g} size="sm" variant="secondary" onClick={() => gate.mutate(g)}>
              check {g.replace("_", " ")}
            </Button>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
