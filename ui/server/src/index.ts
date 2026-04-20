import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { cors } from "hono/cors";
import type { MemoryStore } from "@pw/shared";
import { getProject, listProjects, projectExists } from "./projects.js";
import {
  appendOverride,
  readOverrideMap,
  readStore,
} from "./memory.js";
import { buildAgentGraph, readAgentFile } from "./agents-registry.js";
import { eventHub } from "./events.js";
import { streamSSE } from "hono/streaming";
import {
  launchStage,
  listSessions,
  stopSession,
  STAGES,
  type StageName,
} from "./sdk-driver.js";

const VALID_STORES: MemoryStore[] = [
  "evidence",
  "claims",
  "decisions",
  "tasks",
  "feedback",
  "overrides",
];

const app = new Hono();

app.use(
  "/api/*",
  cors({
    origin: (origin) => {
      if (!origin) return "*";
      if (
        origin.startsWith("http://127.0.0.1:") ||
        origin.startsWith("http://localhost:")
      ) {
        return origin;
      }
      return null;
    },
  }),
);

app.get("/api/health", (c) => c.json({ ok: true }));

app.get("/api/projects", async (c) => {
  const items = await listProjects();
  return c.json({ items });
});

app.get("/api/projects/:name", async (c) => {
  const name = c.req.param("name");
  const project = await getProject(name);
  if (!project) return c.json({ error: "Project not found" }, 404);
  return c.json(project);
});

app.get("/api/projects/:name/memory/:store", async (c) => {
  const name = c.req.param("name");
  const store = c.req.param("store") as MemoryStore;
  if (!VALID_STORES.includes(store)) {
    return c.json({ error: `Unknown store: ${store}` }, 400);
  }
  if (!(await projectExists(name))) {
    return c.json({ error: "Project not found" }, 404);
  }

  const offset = Number(c.req.query("offset") ?? "0") || 0;
  const limitRaw = Number(c.req.query("limit") ?? "500");
  const limit = Math.min(Math.max(limitRaw, 1), 2000);

  const [data, overrides] = await Promise.all([
    readStore(name, store, { offset, limit }),
    store === "overrides" ? Promise.resolve(null) : readOverrideMap(name),
  ]);

  return c.json({
    store,
    total: data.total,
    offset,
    limit,
    items: data.items,
    overrides: overrides
      ? Array.from(overrides.entries()).map(([k, v]) => [k, v])
      : null,
  });
});

app.post("/api/projects/:name/memory/:store/override", async (c) => {
  const name = c.req.param("name");
  const store = c.req.param("store") as MemoryStore;
  if (!VALID_STORES.includes(store) || store === "overrides") {
    return c.json({ error: `Cannot override store: ${store}` }, 400);
  }
  if (!(await projectExists(name))) {
    return c.json({ error: "Project not found" }, 404);
  }

  const body = (await c.req.json().catch(() => ({}))) as {
    target_id?: string;
    status?: string;
    note?: string;
    type?: "override" | "note";
  };
  if (!body.target_id) {
    return c.json({ error: "target_id is required" }, 400);
  }

  const record = await appendOverride(name, {
    type: body.type ?? "override",
    target_id: body.target_id,
    target_store: store,
    status: body.status,
    note: body.note,
    user: "ui",
  });
  return c.json({ ok: true, record });
});

app.get("/api/agents/graph", async (c) => {
  const graph = await buildAgentGraph();
  return c.json(graph);
});

app.get("/api/agents/file", async (c) => {
  const file = c.req.query("path");
  if (!file) return c.json({ error: "path query required" }, 400);
  const body = await readAgentFile(file);
  if (body === null) return c.json({ error: "Not found" }, 404);
  return c.json({ path: file, body });
});

app.post("/api/projects/:name/stages/:stage", async (c) => {
  const name = c.req.param("name");
  const stage = c.req.param("stage") as StageName;
  if (!STAGES.includes(stage)) {
    return c.json({ error: `Unknown stage: ${stage}` }, 400);
  }
  if (!(await projectExists(name))) {
    return c.json({ error: "Project not found" }, 404);
  }
  const body = (await c.req.json().catch(() => ({}))) as {
    args?: string;
    resume?: string;
  };
  try {
    const rec = await launchStage({
      project: name,
      stage,
      args: body.args,
      resume: body.resume,
    });
    return c.json({ ok: true, session: rec });
  } catch (err) {
    return c.json(
      { error: err instanceof Error ? err.message : String(err) },
      500,
    );
  }
});

app.get("/api/sessions", async (c) => {
  const items = await listSessions();
  return c.json({ items });
});

app.post("/api/sessions/:id/stop", async (c) => {
  const id = c.req.param("id");
  const ok = await stopSession(id);
  if (!ok) return c.json({ error: "Session not running" }, 404);
  return c.json({ ok: true });
});

app.get("/api/events/stream", (c) => {
  const project = c.req.query("project") || undefined;
  const replayRaw = Number(c.req.query("replay") ?? "200");
  const replay = Math.min(Math.max(Number.isFinite(replayRaw) ? replayRaw : 200, 0), 2000);

  return streamSSE(c, async (stream) => {
    let closed = false;
    const onClose = () => {
      closed = true;
    };
    c.req.raw.signal.addEventListener("abort", onClose);

    // Replay recent history
    const history = eventHub.recent(project, replay);
    for (const e of history) {
      if (closed) return;
      await stream.writeSSE({ event: "event", data: JSON.stringify(e) });
    }

    await stream.writeSSE({ event: "ready", data: JSON.stringify({ replayed: history.length }) });

    const unsub = eventHub.subscribe((e) => {
      if (closed) return;
      if (project && e.project_hint !== project) return;
      stream.writeSSE({ event: "event", data: JSON.stringify(e) }).catch(() => {
        /* client gone */
      });
    });

    // Heartbeat every 15s to keep the connection alive through proxies
    try {
      while (!closed) {
        await stream.sleep(15_000);
        if (closed) break;
        await stream.writeSSE({ event: "ping", data: String(Date.now()) });
      }
    } finally {
      unsub();
    }
  });
});

const port = Number(process.env.PW_UI_PORT ?? "7777");
const hostname = process.env.PW_UI_HOST ?? "127.0.0.1";

void eventHub.start();

serve({ fetch: app.fetch, port, hostname }, (info) => {
  console.log(`[pw-ui] serving on http://${info.address}:${info.port}`);
});
