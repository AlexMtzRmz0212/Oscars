import { useEffect, useState } from "react";

export type DataState<T> =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ready"; data: T };

/** Loads a JSON file from public/data. */
export function useData<T>(path: string): DataState<T> {
  const [state, setState] = useState<DataState<T>>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });

    fetch(`/data/${path}.json`, { signal: controller.signal })
      .then((response) => {
        // A missing file falls through to the single-page app's index.html, so check the type too.
        const type = response.headers.get("content-type") ?? "";
        if (!response.ok || !type.includes("json")) throw new Error(`${path}: HTTP ${response.status}`);
        return response.json() as Promise<T>;
      })
      .then((data) => setState({ status: "ready", data }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          console.warn(error);
          setState({ status: "error" });
        }
      });

    return () => controller.abort();
  }, [path]);

  return state;
}

/** Loads one precomputed story file. */
export const useStoryData = <T,>(name: string) => useData<T>(`story/${name}`);
