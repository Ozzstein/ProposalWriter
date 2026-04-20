import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Square } from "lucide-react";
import { listSessions, stopSession, type SessionRecord } from "@/lib/api";

const STATUS_VARIANT: Record<
  SessionRecord["status"],
  "warning" | "success" | "destructive" | "muted"
> = {
  running: "warning",
  completed: "success",
  failed: "destructive",
  stopped: "muted",
};

export function SessionsPage(): React.ReactElement {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["sessions"],
    queryFn: listSessions,
    refetchInterval: 2500,
  });

  const stopM = useMutation({
    mutationFn: (id: string) => stopSession(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sessions"] }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sessions</CardTitle>
        <CardDescription>
          SDK-driven stage launches. Sessions are recorded even after the
          server restarts.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-6 text-sm text-foreground-muted">Loading…</div>
        ) : error ? (
          <div className="p-6 text-sm text-destructive">
            Failed to load sessions.
          </div>
        ) : !data || data.length === 0 ? (
          <div className="p-6 text-sm text-foreground-muted">
            No sessions yet. Launch a stage from the Pipeline page.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="border-b border-border text-[11px] uppercase tracking-wide text-foreground-muted">
                <tr>
                  <th className="px-4 py-2 text-left">Started</th>
                  <th className="px-4 py-2 text-left">Project</th>
                  <th className="px-4 py-2 text-left">Stage</th>
                  <th className="px-4 py-2 text-left">Status</th>
                  <th className="px-4 py-2 text-left">SDK session</th>
                  <th className="px-4 py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.map((s) => (
                  <tr key={s.id} className="border-b border-border">
                    <td className="mono px-4 py-2 tabular-nums text-foreground-muted">
                      {s.started_at.replace("T", " ").slice(0, 19)}
                    </td>
                    <td className="mono px-4 py-2">{s.project}</td>
                    <td className="mono px-4 py-2">/{s.stage}</td>
                    <td className="px-4 py-2">
                      <Badge variant={STATUS_VARIANT[s.status]}>
                        {s.status}
                      </Badge>
                    </td>
                    <td className="mono px-4 py-2 text-foreground-muted">
                      {s.sdk_session_id?.slice(0, 8) ?? "—"}
                    </td>
                    <td className="px-4 py-2 text-right">
                      {s.status === "running" ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => stopM.mutate(s.id)}
                          disabled={stopM.isPending}
                          className="gap-1 text-destructive hover:text-destructive"
                          aria-label="Stop session"
                        >
                          <Square className="h-3.5 w-3.5" aria-hidden />
                          Stop
                        </Button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
