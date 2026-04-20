import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** Repository root = two levels up from ui/server/src/ */
export const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");
export const RUNS_DIR = path.join(REPO_ROOT, "runs");
export const AGENTS_DIR = path.join(REPO_ROOT, "agents");
export const COMMANDS_DIR = path.join(REPO_ROOT, ".claude", "commands");
export const EVENTS_FILE = path.join(RUNS_DIR, "_events.jsonl");
export const SERVER_DATA_DIR = path.join(__dirname, "..", "data");

export function projectDir(name: string): string {
  return path.join(RUNS_DIR, name);
}

export function projectMemoryFile(name: string, basename: string): string {
  return path.join(projectDir(name), "memory", basename);
}
