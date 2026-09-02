import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Flag, RotateCw, Search, StickyNote } from "lucide-react";
import { useProjectStore } from "@/stores/project-store";
import { getMemory, postOverride } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import type { MemoryStore, OverrideRecord } from "@pw/shared";

const STORES: { id: MemoryStore; label: string; idField: string; textField: string }[] = [
  { id: "evidence", label: "Sources", idField: "id", textField: "title" },
  { id: "claims", label: "Claims", idField: "id", textField: "text" },
  { id: "gaps", label: "Gaps", idField: "id", textField: "description" },
  { id: "anchors", label: "Novelty", idField: "id", textField: "claim" },
  { id: "sections", label: "Sections", idField: "id", textField: "section_name" },
  { id: "findings", label: "Findings", idField: "id", textField: "section_name" },
  { id: "decisions", label: "Decisions", idField: "id", textField: "decision" },
  { id: "feedback", label: "Feedback", idField: "id", textField: "comment" },
  { id: "tasks", label: "Runs", idField: "id", textField: "stage" },
];

type Row = Record<string, unknown>;

export function MemoryPage(): React.ReactElement {
  const project = useProjectStore((s) => s.activeProject);
  const [active, setActive] = useState<MemoryStore>("evidence");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Row | null>(null);

  const storeMeta = STORES.find((s) => s.id === active)!;
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["memory", project, active],
    queryFn: () => getMemory(project!, active, { limit: 2000 }),
    enabled: Boolean(project),
  });

  const overridesByTarget = useMemo(() => {
    const map = new Map<string, OverrideRecord[]>();
    if (!data?.overrides) return map;
    for (const [key, items] of data.overrides) {
      map.set(key, items as OverrideRecord[]);
    }
    return map;
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [] as Row[];
    const rows = data.items as Row[];
    if (!query) return rows;
    const q = query.toLowerCase();
    return rows.filter((row) => {
      const id = String(row[storeMeta.idField] ?? "").toLowerCase();
      const text = String(row[storeMeta.textField] ?? "").toLowerCase();
      return id.includes(q) || text.includes(q);
    });
  }, [data, query, storeMeta]);

  async function applyOverride(
    target_id: string,
    type: "override" | "note",
    status?: string,
  ): Promise<void> {
    if (!project) return;
    const note = type === "note" ? window.prompt("Note") ?? undefined : undefined;
    if (type === "note" && !note) return;
    await postOverride(project, active, { target_id, type, status, note });
    await queryClient.invalidateQueries({ queryKey: ["memory", project, active] });
  }

  if (!project) {
    return (
      <Card>
        <CardContent>Select a project to browse its memory stores.</CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div
          role="tablist"
          aria-label="Memory store"
          className="flex flex-wrap gap-1 rounded-md border border-border bg-surface p-1"
        >
          {STORES.map((s) => (
            <button
              key={s.id}
              role="tab"
              aria-selected={active === s.id}
              onClick={() => setActive(s.id)}
              className={cn(
                "rounded px-3 py-1 text-xs font-medium transition-colors",
                active === s.id
                  ? "bg-muted text-foreground"
                  : "text-foreground-muted hover:text-foreground",
              )}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div className="relative ml-auto w-full max-w-sm">
          <Search
            className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-muted"
            aria-hidden
          />
          <label htmlFor="memory-search" className="sr-only">
            Search
          </label>
          <input
            id="memory-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search ${storeMeta.label.toLowerCase()}…`}
            className="h-8 w-full rounded-md border border-border bg-background pl-8 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>

        <Button
          size="sm"
          variant="secondary"
          onClick={() => refetch()}
          disabled={isFetching}
          aria-label="Refresh"
        >
          <RotateCw className="h-3.5 w-3.5" aria-hidden />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-baseline gap-2">
            <span>{storeMeta.label}</span>
            <span className="mono text-xs font-normal text-foreground-muted">
              {data ? `${filtered.length} / ${data.total}` : "—"}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 text-sm text-foreground-muted">Loading…</div>
          ) : error ? (
            <div className="p-4 text-sm text-destructive" role="alert">
              Failed to load: {String(error)}
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-4 text-sm text-foreground-muted">
              No records{query ? " match your search" : " yet"}.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {filtered.map((row, i) => {
                const id = String(row[storeMeta.idField] ?? `#${i}`);
                const text = String(row[storeMeta.textField] ?? "");
                const overrides =
                  overridesByTarget.get(`${active}:${id}`) ?? [];
                const latestStatus = overrides.find((o) => o.status)?.status;
                return (
                  <li
                    key={id}
                    className="flex cursor-pointer items-start justify-between gap-4 px-4 py-2.5 hover:bg-muted"
                    onClick={() => setSelected(row)}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="mono text-xs text-foreground-muted">
                          {id}
                        </span>
                        {latestStatus && (
                          <Badge
                            variant={
                              latestStatus === "rejected"
                                ? "destructive"
                                : "info"
                            }
                          >
                            {latestStatus}
                          </Badge>
                        )}
                        {overrides.length > 0 && !latestStatus && (
                          <Badge variant="info">{overrides.length} note(s)</Badge>
                        )}
                      </div>
                      <p className="truncate text-sm">{text || "—"}</p>
                    </div>
                    <div
                      className="flex shrink-0 items-center gap-1"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Button
                        size="sm"
                        variant="ghost"
                        aria-label={`Flag ${id} as rejected`}
                        onClick={() =>
                          applyOverride(id, "override", "rejected")
                        }
                      >
                        <Flag className="h-3.5 w-3.5" aria-hidden />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        aria-label={`Add note to ${id}`}
                        onClick={() => applyOverride(id, "note")}
                      >
                        <StickyNote className="h-3.5 w-3.5" aria-hidden />
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      {selected && (
        <RecordDrawer
          row={selected}
          overrides={
            overridesByTarget.get(
              `${active}:${String(selected[storeMeta.idField])}`,
            ) ?? []
          }
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}

function RecordDrawer({
  row,
  overrides,
  onClose,
}: {
  row: Row;
  overrides: OverrideRecord[];
  onClose: () => void;
}): React.ReactElement {
  return (
    <div
      className="fixed inset-0 z-40 flex justify-end bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="h-full w-full max-w-xl overflow-auto border-l border-border bg-surface p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold">Record</h2>
          <Button size="sm" variant="ghost" onClick={onClose} aria-label="Close">
            Close
          </Button>
        </div>
        <pre className="mono overflow-x-auto rounded bg-background p-3 text-xs">
          {JSON.stringify(row, null, 2)}
        </pre>
        {overrides.length > 0 && (
          <>
            <h3 className="mt-4 text-sm font-semibold">Overrides / notes</h3>
            <ul className="mt-2 space-y-2">
              {overrides.map((o, i) => (
                <li
                  key={i}
                  className="rounded border border-border bg-background p-2 text-xs"
                >
                  <div className="mono text-foreground-muted">{o.ts}</div>
                  {o.status && (
                    <div>
                      <Badge
                        variant={
                          o.status === "rejected" ? "destructive" : "info"
                        }
                      >
                        {o.status}
                      </Badge>
                    </div>
                  )}
                  {o.note && <div className="mt-1">{o.note}</div>}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
