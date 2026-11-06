import { useEffect, useState } from "react";

const LONGEST_WAIT_MS = 1200;

/** Becomes true once the browser has a spare moment, or after a short wait if it never does. */
export function useIdle() {
  const [idle, setIdle] = useState(false);

  useEffect(() => {
    if ("requestIdleCallback" in window) {
      const handle = window.requestIdleCallback(() => setIdle(true), { timeout: LONGEST_WAIT_MS });
      return () => window.cancelIdleCallback(handle);
    }
    const timer = setTimeout(() => setIdle(true), 0);
    return () => clearTimeout(timer);
  }, []);

  return idle;
}
