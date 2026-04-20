import fs from "node:fs";
import fsp from "node:fs/promises";
import { EVENTS_FILE, RUNS_DIR } from "./paths.js";
import type { PipelineEvent } from "@pw/shared";

let ensured = false;

async function ensureRuns(): Promise<void> {
  if (ensured) return;
  await fsp.mkdir(RUNS_DIR, { recursive: true });
  ensured = true;
}

/** Append one event to runs/_events.jsonl. The tailer in events.ts picks it up. */
export async function appendEvent(
  partial: Omit<PipelineEvent, "ts"> & { ts?: string },
): Promise<void> {
  await ensureRuns();
  const event: PipelineEvent = {
    ts: partial.ts ?? new Date().toISOString(),
    ...partial,
  } as PipelineEvent;
  const line = JSON.stringify(event) + "\n";
  await new Promise<void>((resolve) => {
    fs.open(EVENTS_FILE, "a", (err, fd) => {
      if (err) return resolve();
      fs.write(fd, line, () => {
        fs.close(fd, () => resolve());
      });
    });
  });
}
