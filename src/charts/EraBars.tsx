import { formatPercent } from "../lib/format";
import "./EraBars.css";

export interface EraBar {
  era: string;
  share: number;
  /** Extra context for small samples, such as "1 of 6". */
  detail?: string;
}

/** Five short columns, one per era, with the value on each cap. */
export function EraBars({ bars, label }: { bars: EraBar[]; label: string }) {
  return (
    <ul className="era-bars" aria-label={label}>
      {bars.map((bar) => (
        <li key={bar.era}>
          <span className="era-bar-track">
            <span className="era-bar-value">{formatPercent(bar.share)}</span>
            <span className="era-bar-fill" style={{ height: `${Math.max(bar.share * 100, 2)}%` }} />
          </span>
          <span className="era-bar-label">{bar.era}</span>
          {bar.detail && <span className="era-bar-detail">{bar.detail}</span>}
        </li>
      ))}
    </ul>
  );
}
