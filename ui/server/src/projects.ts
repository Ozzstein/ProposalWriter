import { readFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import type { ProjectState, ProjectSummary, MemoryCounts } from "@pw/shared";
import { RUNS_DIR, projectDir, projectMemoryFile } from "./paths.js";
import { countLines, fileExists } from "./jsonl.js";

async function readState(name: string): Promise<ProjectState | null> {
  const statePath = path.join(projectDir(name), "state.json");
  if (!(await fileExists(statePath))) return null;
  try {
    const raw = await readFile(statePath, "utf8");
    return JSON.parse(raw) as ProjectState;
  } catch {
    return null;
  }
}

async function readMemoryCounts(name: string): Promise<MemoryCounts> {
  const [evidence, claims, decisions, tasks, feedback, overrides] =
    await Promise.all([
      countLines(projectMemoryFile(name, "evidence_store.jsonl")),
      countLines(projectMemoryFile(name, "claim_registry.jsonl")),
      countLines(projectMemoryFile(name, "decision_log.jsonl")),
      countLines(projectMemoryFile(name, "task_registry.jsonl")),
      countLines(projectMemoryFile(name, "feedback_log.jsonl")),
      countLines(projectMemoryFile(name, "overrides.jsonl")),
    ]);
  return { evidence, claims, decisions, tasks, feedback, overrides };
}

export async function listProjects(): Promise<ProjectSummary[]> {
  if (!(await fileExists(RUNS_DIR))) return [];
  const entries = await readdir(RUNS_DIR, { withFileTypes: true });
  const names = entries
    .filter((e) => e.isDirectory() && !e.name.startsWith("_") && !e.name.startsWith("."))
    .map((e) => e.name);

  const summaries: ProjectSummary[] = [];
  for (const name of names) {
    const state = await readState(name);
    if (!state) continue;
    const memory = await readMemoryCounts(name);
    summaries.push({ name, state, memory });
  }

  summaries.sort((a, b) => {
    const ad = a.state.created_at ?? "";
    const bd = b.state.created_at ?? "";
    return bd.localeCompare(ad);
  });
  return summaries;
}

export async function getProject(name: string): Promise<ProjectSummary | null> {
  const state = await readState(name);
  if (!state) return null;
  const memory = await readMemoryCounts(name);
  return { name, state, memory };
}

export async function projectExists(name: string): Promise<boolean> {
  try {
    const s = await stat(projectDir(name));
    return s.isDirectory();
  } catch {
    return false;
  }
}
