import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  type Edge,
  type Node,
} from "reactflow";
import { getAgentFile, getAgentGraph } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AgentGraph, AgentKind, AgentNode } from "@pw/shared";
import { useEventStore } from "@/stores/event-store";

const PULSE_WINDOW_MS = 30_000;

const KIND_ORDER: AgentKind[] = [
  "stage",
  "orchestrator",
  "interviewer",
  "retriever",
  "synthesizer",
  "writer",
  "modeler",
  "renderer",
  "reviewer",
];

const KIND_COLOR: Record<AgentKind, string> = {
  stage: "#0ea5e9",
  orchestrator: "#22c55e",
  interviewer: "#14b8a6",
  retriever: "#f59e0b",
  synthesizer: "#a855f7",
  writer: "#ec4899",
  modeler: "#84cc16",
  renderer: "#94a3b8",
  reviewer: "#ef4444",
};

function emptyByKind(): Record<AgentKind, AgentNode[]> {
  return Object.fromEntries(KIND_ORDER.map((k) => [k, []])) as unknown as Record<AgentKind, AgentNode[]>;
}

function layoutNodes(graph: AgentGraph, pulses: Record<string, number>, now: number): Node[] {
  const columns = emptyByKind();
  for (const node of graph.nodes) {
    columns[node.kind].push(node);
  }

  const columnOrder = KIND_ORDER.filter((k) => columns[k].length > 0);
  const colWidth = 260;
  const rowHeight = 64;

  const result: Node[] = [];
  columnOrder.forEach((kind, colIdx) => {
    columns[kind].forEach((node, rowIdx) => {
      const lastSeen = pulses[node.id];
      const active =
        typeof lastSeen === "number" && now - lastSeen < PULSE_WINDOW_MS;
      result.push({
        id: node.id,
        position: { x: colIdx * colWidth, y: rowIdx * rowHeight },
        data: {
          label: node.title,
          kind: node.kind,
          model: node.model,
          file: node.file,
          description: node.description,
        },
        className: active ? "pw-node-active" : undefined,
        style: {
          background: "var(--color-surface)",
          color: "var(--color-foreground)",
          border: `1px solid ${active ? "#22c55e" : KIND_COLOR[kind]}`,
          borderRadius: 8,
          fontSize: 12,
          padding: 8,
          width: 220,
          boxShadow: active ? "0 0 0 2px #22c55e55, 0 0 12px #22c55e88" : undefined,
        },
      });
    });
  });
  return result;
}

function toEdges(graph: AgentGraph): Edge[] {
  return graph.edges.map((e, i) => ({
    id: `e${i}`,
    source: e.from,
    target: e.to,
    markerEnd: { type: MarkerType.ArrowClosed, color: "#475569" },
    style: { stroke: "#475569", strokeWidth: 1.5 },
  }));
}

export function GraphPage(): React.ReactElement {
  const { data, isLoading, error } = useQuery({
    queryKey: ["agent-graph"],
    queryFn: getAgentGraph,
  });

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const pulses = useEventStore((s) => s.agentPulse);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 5_000);
    return () => clearInterval(id);
  }, []);

  const nodes = useMemo(
    () => (data ? layoutNodes(data, pulses, Date.now()) : []),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, pulses, tick],
  );
  const edges = useMemo(() => (data ? toEdges(data) : []), [data]);

  const selectedNode = useMemo(() => {
    if (!data || !selectedId) return null;
    return data.nodes.find((n) => n.id === selectedId) ?? null;
  }, [data, selectedId]);

  if (isLoading) {
    return (
      <Card>
        <CardContent>Loading agent graph…</CardContent>
      </Card>
    );
  }
  if (error || !data) {
    return (
      <Card>
        <CardContent className="text-destructive">
          Failed to load graph: {String(error)}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4 lg:h-[calc(100vh-9rem)] lg:flex-row">
      <Card className="flex-1 overflow-hidden lg:min-w-0">
        <CardHeader>
          <CardTitle>Agent system</CardTitle>
          <CardDescription>
            Commands → orchestrators → workers. Click any node to inspect its
            definition.
          </CardDescription>
          <Legend />
        </CardHeader>
        <CardContent className="h-[70vh] p-0 lg:h-full">
          {/* Graph view — shown on >=lg, list fallback below */}
          <div className="hidden h-full lg:block">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              fitView
              proOptions={{ hideAttribution: true }}
              onNodeClick={(_, node) => setSelectedId(node.id)}
            >
              <Background
                variant={BackgroundVariant.Dots}
                gap={16}
                size={1}
                color="#334155"
              />
              <Controls />
            </ReactFlow>
          </div>
          <GroupedList
            graph={data}
            onSelect={setSelectedId}
            selectedId={selectedId}
            className="lg:hidden"
          />
        </CardContent>
      </Card>

      {selectedNode && (
        <AgentDetail
          node={selectedNode}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}

function Legend(): React.ReactElement {
  return (
    <div className="flex flex-wrap gap-2 pt-1">
      {KIND_ORDER.map((kind) => (
        <span
          key={kind}
          className="inline-flex items-center gap-1.5 text-[11px] text-foreground-muted"
        >
          <span
            aria-hidden
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: KIND_COLOR[kind] }}
          />
          {kind}
        </span>
      ))}
    </div>
  );
}

function GroupedList({
  graph,
  onSelect,
  selectedId,
  className,
}: {
  graph: AgentGraph;
  onSelect: (id: string) => void;
  selectedId: string | null;
  className?: string;
}): React.ReactElement {
  const byKind = emptyByKind();
  for (const n of graph.nodes) byKind[n.kind].push(n);

  return (
    <div className={className}>
      {KIND_ORDER.filter((k) => byKind[k].length > 0).map((kind) => (
        <section key={kind} className="border-b border-border p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-foreground-muted">
            {kind}
          </h3>
          <ul className="space-y-1">
            {byKind[kind].map((n) => (
              <li key={n.id}>
                <button
                  onClick={() => onSelect(n.id)}
                  className={`w-full rounded px-2 py-1 text-left text-sm hover:bg-muted ${
                    selectedId === n.id ? "bg-muted" : ""
                  }`}
                >
                  {n.title}
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

function AgentDetail({
  node,
  onClose,
}: {
  node: AgentNode;
  onClose: () => void;
}): React.ReactElement {
  const [body, setBody] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    getAgentFile(node.file)
      .then((b) => {
        if (alive) setBody(b);
      })
      .catch(() => {
        if (alive) setBody(null);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [node.file]);

  return (
    <Card className="lg:w-96 lg:shrink-0 lg:overflow-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{node.title}</CardTitle>
          <Button size="sm" variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Badge variant="muted">{node.kind}</Badge>
          {node.model && <Badge variant="info">{node.model}</Badge>}
        </div>
        <CardDescription>{node.description}</CardDescription>
        <div className="mono text-[11px] text-foreground-muted">{node.file}</div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-sm text-foreground-muted">Loading…</div>
        ) : body ? (
          <pre className="mono overflow-x-auto whitespace-pre-wrap text-xs leading-relaxed">
            {body}
          </pre>
        ) : (
          <div className="text-sm text-destructive">File not found.</div>
        )}
      </CardContent>
    </Card>
  );
}
