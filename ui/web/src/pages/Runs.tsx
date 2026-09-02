import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Square } from "lucide-react";
import { getRun, listRuns, stopRun } from "@/lib/api";
import { useProjectStore } from "@/stores/project-store";
import type { JobStatus, RunStatus } from "@pw/shared";

const RUN_VARIANT: Record<RunStatus, "warning" | "success" | "destructive" | "muted" | "info"> = {
  queued: "muted",
  running: "warning",
  waiting_for_user: "info",
  completed: "success",
  failed: "destructive",
  stopped: "muted",
  interrupted: "muted",
};

const JOB_VARIANT: Record<JobStatus, "warning" | "success" | "destructive" | "muted" | "info"> = {
  pending: "muted",
  ready: "muted",
  running: "warning",
  waiting: "info",
  completed: "success",
  failed: "destructive",
  skipped: "muted",
  interrupted: "muted",
};

export function RunsPage(): React.ReactElement {
  const active = useProjectStore((s) => s.activeProject);
  const qc = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);
  const { data, isLoading, error } = useQuery({
    queryKey: ["runs", active],
    queryFn: () => listRuns(active ?? undefined),
    refetchInterval: 2500,
  });
  const detail = useQuery({
    queryKey: ["run", selected],
    queryFn: () => getRun(selected!),
    enabled: !!selected,
    refetchInterval: 2500,
  });
  const stopM = useMutation({
    mutationFn: (id: string) => stopRun(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runs"] }),
  });

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Runs</CardTitle>
          <CardDescription>Every stage run with its job DAG, cost and outcome. Runs survive server restarts.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-foreground-muted">Loading…</div>
          ) : error ? (
            <div className="p-6 text-sm text-destructive">{String(error)}</div>
          ) : (
            <table className="w-full text-xs">
              <thead className="text-left text-foreground-muted">
                <tr>
                  <th className="px-4 py-2">Stage</th>
                  <th className="px-2 py-2">Status</th>
                  <th className="px-2 py-2">Phase</th>
                  <th className="px-2 py-2">Cost</th>
                  <th className="px-2 py-2">Started</th>
                  <th className="px-2 py-2" />
                </tr>
              </thead>
              <tbody>
                {(data ?? []).map((r) => (
                  <tr key={r.id} className={`cursor-pointer border-t border-border hover:bg-muted ${selected === r.id ? "bg-muted" : ""}`} onClick={() => setSelected(r.id)}>
                    <td className="px-4 py-2 font-medium">{r.stage}</td>
                    <td className="px-2 py-2"><Badge variant={RUN_VARIANT[r.status]}>{r.status.replace("_", " ")}</Badge></td>
                    <td className="mono px-2 py-2 text-foreground-muted">{r.phase ?? "—"}</td>
                    <td className="mono px-2 py-2">${r.cost_usd.toFixed(2)}</td>
                    <td className="mono px-2 py-2 text-foreground-muted">{(r.started_at ?? r.created_at).slice(0, 16).replace("T", " ")}</td>
                    <td className="px-2 py-2">
                      {(r.status === "running" || r.status === "waiting_for_user") && (
                        <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); stopM.mutate(r.id); }}>
                          <Square className="h-3 w-3" aria-hidden /> stop
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{selected ? `Run ${selected}` : "Jobs"}</CardTitle>
          <CardDescription>{detail.data?.run.summary ?? detail.data?.run.error ?? "Select a run to see its jobs."}</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {detail.data && (
            <ul>
              {detail.data.jobs.map((j) => (
                <li key={j.id} className="border-t border-border px-4 py-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="mono font-medium">{j.name}</span>
                    <Badge variant={JOB_VARIANT[j.status]}>{j.status}</Badge>
                    {j.contract && <span className="text-foreground-muted">{j.contract}</span>}
                    <span className="ml-auto mono">${j.cost_usd.toFixed(2)}</span>
                  </div>
                  {j.deps.length > 0 && <div className="text-[11px] text-foreground-muted">after: {j.deps.join(", ")}</div>}
                  {j.result?.summary != null && <div className="text-[11px]">{String(j.result.summary)}</div>}
                  {j.error && <pre className="mono mt-1 whitespace-pre-wrap text-[11px] text-destructive">{j.error.split("\n")[0]}</pre>}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
