import { demoData } from "./data";
import type { AegisData } from "./types";

async function read<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`/api/v1${path}`, { headers: { Accept: "application/json" } });
    if (!response.ok) return fallback;
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export function loadConsoleData(): Promise<AegisData> {
  return read<AegisData>("/console", demoData);
}
