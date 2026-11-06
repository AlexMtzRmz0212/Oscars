import { useEffect, useRef, useState } from "react";
import "./ChartTip.css";

/** The width below which a story's chart pins to the top of the screen. Matches ScrollStory.css. */
export const PINNED_TOP_WIDTH = 900;

interface Options {
  /** Height as a share of width, before the screen limits it. */
  ratio?: number;
  /** Share of screen height the chart may take when pinned to the top. */
  pinnedShare?: number;
  /** Pixels kept free for the legend and margins when the chart sits beside the slips. */
  reserved?: number;
}

/** Measures a chart's slot so SVG text stays a real size instead of scaling with a viewBox. */
export function useChartSize({ ratio = 0.7, pinnedShare = 0.42, reserved = 190 }: Options = {}) {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const measure = () => {
      const width = element.clientWidth;
      const pinned = window.innerWidth <= PINNED_TOP_WIDTH;
      const limit = pinned ? window.innerHeight * pinnedShare : window.innerHeight - reserved;
      const height = Math.round(Math.min(width * ratio, limit));
      setSize((previous) => (previous.width === width && previous.height === height ? previous : { width, height }));
    };

    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [ratio, pinnedShare, reserved]);

  return { ref, ...size };
}
