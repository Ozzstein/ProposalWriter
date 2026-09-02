import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Play, RotateCcw, ShieldCheck } from "lucide-react";
import { getProject, listRuns, listStages, runGate, startRun } from "@/lib/api";
import { useProjectStore } from "@/stores/project-store";
import type { StageDef } from "@pw/shared";
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
      <div className="grid gap-3 md:grid-cols-2">
        {(stages ?? []).map((s: StageDef) => {
          const last = runs?.find((r) => r.stage === s.name);
          const stateStatus = s.state_key ? project?.state.stages[s.state_key]?.status : undefined;
          const gateOk = s.requires_gate ? project?.state.gates[s.requires_gate]?.passed : true;
          return (
            <Card key={s.name}>
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-base">{s.name}</CardTitle>
                  <StageBadge status={stateStatus} />
                </div>
                <CardDescription>{s.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
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
                  <Button size="sm" disabled={!!activeRun || start.isPending} onClick={() => start.mutate({ stage: s.name })}>
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
