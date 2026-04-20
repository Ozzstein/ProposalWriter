import { create } from "zustand";
import type { PipelineEvent } from "@pw/shared";

const CAPACITY = 2000;

interface EventStoreState {
  events: PipelineEvent[];
  status: "idle" | "connecting" | "live" | "paused" | "error";
  lastPingAt: number | null;
  paused: boolean;
  agentPulse: Record<string, number>;
  push: (event: PipelineEvent) => void;
  setStatus: (status: EventStoreState["status"]) => void;
  setLastPingAt: (ts: number) => void;
  setPaused: (paused: boolean) => void;
  clear: () => void;
}

export const useEventStore = create<EventStoreState>((set) => ({
  events: [],
  status: "idle",
  lastPingAt: null,
  paused: false,
  agentPulse: {},
  push: (event) =>
    set((state) => {
      const next = state.events.concat(event);
      if (next.length > CAPACITY) next.splice(0, next.length - CAPACITY);
      const pulse = { ...state.agentPulse };
      if (event.agent_hint) {
        pulse[event.agent_hint] = Date.parse(event.ts) || Date.now();
      }
      return { events: next, agentPulse: pulse };
    }),
  setStatus: (status) => set({ status }),
  setLastPingAt: (ts) => set({ lastPingAt: ts }),
  setPaused: (paused) => set({ paused }),
  clear: () => set({ events: [], agentPulse: {} }),
}));
