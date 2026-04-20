import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "@/lib/api";
import { useProjectStore } from "@/stores/project-store";
import { FolderKanban } from "lucide-react";

export function ProjectSwitcher(): React.ReactElement {
  const activeProject = useProjectStore((s) => s.activeProject);
  const setActiveProject = useProjectStore((s) => s.setActiveProject);

  const { data, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    refetchInterval: 15_000,
  });

  useEffect(() => {
    if (!activeProject && data && data.length > 0) {
      setActiveProject(data[0]!.name);
    }
  }, [activeProject, data, setActiveProject]);

  if (error) {
    return (
      <div className="text-xs text-destructive" role="alert">
        Backend unreachable — is the dev server running on :7777?
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <FolderKanban
        className="h-4 w-4 text-foreground-muted"
        aria-hidden
      />
      <label className="sr-only" htmlFor="project-switcher">
        Active project
      </label>
      <select
        id="project-switcher"
        className="h-8 rounded-md border border-border bg-background px-2 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={activeProject ?? ""}
        onChange={(e) => setActiveProject(e.target.value || null)}
        disabled={isLoading}
      >
        {isLoading ? (
          <option>Loading…</option>
        ) : !data || data.length === 0 ? (
          <option value="">No projects in runs/</option>
        ) : (
          data.map((p) => (
            <option key={p.name} value={p.name}>
              {p.state.project_title ?? p.name}
            </option>
          ))
        )}
      </select>
      {activeProject && (
        <span className="mono text-[11px] text-foreground-muted">
          {activeProject}
        </span>
      )}
    </div>
  );
}
