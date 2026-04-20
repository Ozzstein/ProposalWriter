import fs from "node:fs";
import fsp from "node:fs/promises";
import readline from "node:readline";
import { EVENTS_FILE } from "./paths.js";
import type { PipelineEvent } from "@pw/shared";

type Subscriber = (event: PipelineEvent) => void;

const RING_CAPACITY = 2000;

class EventHub {
  private ring: PipelineEvent[] = [];
  private subs = new Set<Subscriber>();
  private position = 0;
  private watcher: fs.FSWatcher | null = null;
  private reading = false;
  private pendingReRead = false;
  private carry = "";
  private started = false;

  async start(): Promise<void> {
    if (this.started) return;
    this.started = true;
    try {
      const stat = await fsp.stat(EVENTS_FILE);
      this.position = stat.size;
    } catch {
      this.position = 0;
    }
    this.attachWatcher();
  }

  private attachWatcher(): void {
    try {
      this.watcher = fs.watch(EVENTS_FILE, { persistent: false }, () => {
        this.scheduleRead();
      });
      this.watcher.on("error", () => {
        // File may not exist yet; retry in 2s
        this.watcher?.close();
        this.watcher = null;
        setTimeout(() => this.attachWatcher(), 2000);
      });
    } catch {
      setTimeout(() => this.attachWatcher(), 2000);
    }
  }

  private scheduleRead(): void {
    if (this.reading) {
      this.pendingReRead = true;
      return;
    }
    void this.readNew();
  }

  private async readNew(): Promise<void> {
    this.reading = true;
    try {
      let stat: fs.Stats;
      try {
        stat = await fsp.stat(EVENTS_FILE);
      } catch {
        return;
      }
      if (stat.size < this.position) {
        // File truncated/rotated — reset
        this.position = 0;
        this.carry = "";
      }
      if (stat.size === this.position) return;

      const stream = fs.createReadStream(EVENTS_FILE, {
        start: this.position,
        end: stat.size - 1,
        encoding: "utf8",
      });
      let chunkBuf = this.carry;
      for await (const chunk of stream) {
        chunkBuf += chunk;
        const lines = chunkBuf.split("\n");
        chunkBuf = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.trim()) continue;
          this.ingestLine(line);
        }
      }
      this.carry = chunkBuf;
      this.position = stat.size;
    } finally {
      this.reading = false;
      if (this.pendingReRead) {
        this.pendingReRead = false;
        this.scheduleRead();
      }
    }
  }

  private ingestLine(line: string): void {
    let parsed: PipelineEvent;
    try {
      parsed = JSON.parse(line) as PipelineEvent;
    } catch {
      return;
    }
    this.ring.push(parsed);
    if (this.ring.length > RING_CAPACITY) {
      this.ring.splice(0, this.ring.length - RING_CAPACITY);
    }
    for (const sub of this.subs) {
      try {
        sub(parsed);
      } catch {
        /* subscriber error — isolate */
      }
    }
  }

  /** Return up to `n` most recent events, optionally filtered by project. */
  recent(project?: string, n = 200): PipelineEvent[] {
    const slice = this.ring.slice(-Math.max(1, Math.min(n, RING_CAPACITY)));
    if (!project) return slice;
    return slice.filter((e) => e.project_hint === project);
  }

  subscribe(fn: Subscriber): () => void {
    this.subs.add(fn);
    return () => {
      this.subs.delete(fn);
    };
  }
}

export const eventHub = new EventHub();
