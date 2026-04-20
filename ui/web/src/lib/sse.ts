import { useEffect } from "react";
import type { PipelineEvent } from "@pw/shared";
import { useEventStore } from "@/stores/event-store";

/** Open (and maintain) a single EventSource for the given project. */
export function useEventStream(project: string | null): void {
  const setStatus = useEventStore((s) => s.setStatus);
  const setLastPingAt = useEventStore((s) => s.setLastPingAt);
  const push = useEventStore((s) => s.push);
  const clear = useEventStore((s) => s.clear);

  useEffect(() => {
    clear();
    setStatus("connecting");

    const qs = new URLSearchParams();
    if (project) qs.set("project", project);
    const url = `/api/events/stream${qs.toString() ? `?${qs}` : ""}`;
    const es = new EventSource(url);

    const onEvent = (ev: MessageEvent) => {
      try {
        const parsed = JSON.parse(ev.data) as PipelineEvent;
        // Respect pause inline — read fresh pause state each tick
        if (useEventStore.getState().paused) return;
        push(parsed);
      } catch {
        /* ignore malformed */
      }
    };

    const onReady = () => {
      setStatus("live");
    };

    const onPing = (ev: MessageEvent) => {
      setLastPingAt(Number(ev.data) || Date.now());
    };

    const onError = () => {
      setStatus("error");
    };

    es.addEventListener("event", onEvent as EventListener);
    es.addEventListener("ready", onReady as EventListener);
    es.addEventListener("ping", onPing as EventListener);
    es.addEventListener("error", onError as EventListener);

    return () => {
      es.removeEventListener("event", onEvent as EventListener);
      es.removeEventListener("ready", onReady as EventListener);
      es.removeEventListener("ping", onPing as EventListener);
      es.removeEventListener("error", onError as EventListener);
      es.close();
      setStatus("idle");
    };
  }, [project, clear, push, setLastPingAt, setStatus]);
}
