import { NavLink, Outlet } from "react-router-dom";
import {
  Activity,
  Database,
  Inbox,
  LayoutDashboard,
  ListChecks,
  Network,
  Plus,
  Workflow,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { listInbox } from "@/lib/api";
import { cn } from "@/lib/cn";
import { ProjectSwitcher } from "./ProjectSwitcher";
import { useEventStream } from "@/lib/sse";
import { useProjectStore } from "@/stores/project-store";
import { useEventStore } from "@/stores/event-store";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/pipeline", label: "Pipeline", icon: Workflow },
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/runs", label: "Runs", icon: ListChecks },
  { to: "/activity", label: "Activity", icon: Activity },
  { to: "/agents", label: "Agents", icon: Network },
  { to: "/graph", label: "Graph", icon: Database },
  { to: "/new", label: "New project", icon: Plus },
];

export function AppShell(): React.ReactElement {
  const activeProject = useProjectStore((s) => s.activeProject);
  useEventStream(activeProject);
  const status = useEventStore((s) => s.status);
  const pending = useQuery({
    queryKey: ["inbox-count", activeProject],
    queryFn: () => listInbox(activeProject ?? undefined),
    refetchInterval: 3000,
  });
  const pendingCount = pending.data?.length ?? 0;

  const statusColor =
    status === "live"
      ? "bg-accent shadow-[0_0_10px_var(--color-accent)]"
      : status === "error"
        ? "bg-destructive"
        : status === "connecting"
          ? "bg-warning animate-pulse"
          : "bg-border";
  const statusLabel =
    status === "live"
      ? "Live"
      : status === "error"
        ? "Disconnected"
        : status === "connecting"
          ? "Connecting"
          : "Idle";

  return (
    <div className="flex h-full min-h-screen bg-background text-foreground">
      <aside
        className="flex w-56 shrink-0 flex-col border-r border-border bg-surface"
        aria-label="Primary"
      >
        <div className="flex h-14 items-center gap-2 border-b border-border px-4">
          <span
            aria-hidden
            className="h-2 w-2 rounded-full bg-accent shadow-[0_0_10px_var(--color-accent)]"
          />
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold">Mission Control</span>
            <span className="text-[11px] text-foreground-muted">
              local workspace
            </span>
          </div>
        </div>

        <nav className="flex flex-col gap-0.5 p-2">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors",
                  isActive
                    ? "bg-muted text-foreground"
                    : "text-foreground-muted hover:bg-muted hover:text-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" aria-hidden />
              <span>{label}</span>
              {to === "/inbox" && pendingCount > 0 && (
                <span className="ml-auto rounded-full bg-destructive px-1.5 text-[10px] text-white">{pendingCount}</span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto p-3 text-[11px] text-foreground-muted">
          <div>Local · 127.0.0.1</div>
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center gap-4 border-b border-border bg-surface px-4">
          <ProjectSwitcher />
          <div
            className="ml-auto flex items-center gap-2 text-[11px] text-foreground-muted"
            aria-live="polite"
            aria-atomic="true"
          >
            <span
              aria-hidden
              className={cn("h-2 w-2 rounded-full", statusColor)}
            />
            <span>Feed: {statusLabel}</span>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
