import { useEffect } from "react";

const SETTLE_MS = 5000;

/**
 * Opening a link like /#the-money lands on that act. The page grows as each act's data arrives, so
 * this keeps the target in place while it settles, and lets go the moment the visitor starts scrolling.
 */
export function useHashScroll() {
  useEffect(() => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (!id) return;

    const align = () => document.getElementById(id)?.scrollIntoView({ behavior: "instant", block: "start" });
    const observer = new ResizeObserver(align);
    const stop = () => {
      observer.disconnect();
      window.removeEventListener("wheel", stop);
      window.removeEventListener("touchstart", stop);
      window.removeEventListener("keydown", stop);
    };

    observer.observe(document.body);
    window.addEventListener("wheel", stop, { passive: true });
    window.addEventListener("touchstart", stop, { passive: true });
    window.addEventListener("keydown", stop);
    const timer = setTimeout(stop, SETTLE_MS);

    return () => {
      clearTimeout(timer);
      stop();
    };
  }, []);
}
