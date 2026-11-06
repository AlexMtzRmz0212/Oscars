import type { ReactNode } from "react";
import { clamp } from "./scales";
import "./ChartTip.css";

const SIDE_ROOM = 90;

interface Props {
  x: number;
  y: number;
  chartWidth: number;
  value: ReactNode;
  children: ReactNode;
}

/** The value leads and the label follows, because the reader already knows the series. */
export function ChartTip({ x, y, chartWidth, value, children }: Props) {
  return (
    <div className="chart-tip" role="status" style={{ left: clamp(x, SIDE_ROOM, chartWidth - SIDE_ROOM), top: y }}>
      <strong>{value}</strong>
      <span>{children}</span>
    </div>
  );
}
