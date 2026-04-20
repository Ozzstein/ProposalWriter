import type { MemoryStore, OverrideRecord } from "@pw/shared";
import { projectMemoryFile } from "./paths.js";
import { appendJsonl, readJsonl } from "./jsonl.js";

const STORE_FILE: Record<MemoryStore, string> = {
  evidence: "evidence_store.jsonl",
  claims: "claim_registry.jsonl",
  decisions: "decision_log.jsonl",
  tasks: "task_registry.jsonl",
  feedback: "feedback_log.jsonl",
  overrides: "overrides.jsonl",
};

export function memoryFilePath(project: string, store: MemoryStore): string {
  return projectMemoryFile(project, STORE_FILE[store]);
}

export async function readStore(
  project: string,
  store: MemoryStore,
  opts: { offset?: number; limit?: number } = {},
): Promise<{ items: unknown[]; total: number }> {
  return readJsonl(memoryFilePath(project, store), opts);
}

export async function readOverrideMap(
  project: string,
): Promise<Map<string, OverrideRecord[]>> {
  const { items } = await readJsonl<OverrideRecord>(
    memoryFilePath(project, "overrides"),
  );
  const map = new Map<string, OverrideRecord[]>();
  for (const item of items) {
    if (!item || typeof item !== "object") continue;
    const key = `${item.target_store}:${item.target_id}`;
    const list = map.get(key) ?? [];
    list.push(item);
    map.set(key, list);
  }
  return map;
}

export async function appendOverride(
  project: string,
  record: Omit<OverrideRecord, "ts">,
): Promise<OverrideRecord> {
  const full: OverrideRecord = { ...record, ts: new Date().toISOString() };
  await appendJsonl(memoryFilePath(project, "overrides"), full);
  return full;
}
