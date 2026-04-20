import { createReadStream } from "node:fs";
import { createInterface } from "node:readline";
import { access, appendFile, mkdir } from "node:fs/promises";
import path from "node:path";

export async function fileExists(p: string): Promise<boolean> {
  try {
    await access(p);
    return true;
  } catch {
    return false;
  }
}

export async function countLines(filePath: string): Promise<number> {
  if (!(await fileExists(filePath))) return 0;
  return new Promise((resolve, reject) => {
    let count = 0;
    const rl = createInterface({
      input: createReadStream(filePath, { encoding: "utf8" }),
      crlfDelay: Infinity,
    });
    rl.on("line", (line) => {
      if (line.trim().length > 0) count += 1;
    });
    rl.on("close", () => resolve(count));
    rl.on("error", reject);
  });
}

export async function readJsonl<T = unknown>(
  filePath: string,
  opts: { offset?: number; limit?: number } = {},
): Promise<{ items: T[]; total: number }> {
  const { offset = 0, limit = Infinity } = opts;
  if (!(await fileExists(filePath))) return { items: [], total: 0 };

  return new Promise((resolve, reject) => {
    const items: T[] = [];
    let total = 0;
    const rl = createInterface({
      input: createReadStream(filePath, { encoding: "utf8" }),
      crlfDelay: Infinity,
    });
    rl.on("line", (line) => {
      const trimmed = line.trim();
      if (!trimmed) return;
      const index = total;
      total += 1;
      if (index < offset) return;
      if (items.length >= limit) return;
      try {
        items.push(JSON.parse(trimmed) as T);
      } catch {
        items.push({ __parse_error: true, __raw: trimmed } as unknown as T);
      }
    });
    rl.on("close", () => resolve({ items, total }));
    rl.on("error", reject);
  });
}

export async function appendJsonl(
  filePath: string,
  record: unknown,
): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  await appendFile(filePath, JSON.stringify(record) + "\n", "utf8");
}
