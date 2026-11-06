import { useMemo, useRef, useState } from "react";
import type { CSSProperties, KeyboardEvent, PointerEvent } from "react";
import { ChartTip } from "../../charts/ChartTip";
import { formatCount, plural } from "../../lib/format";
import type { SweepCell, SweepData } from "../../lib/types";
import type { SweepStep } from "./sweepSteps";
import "./SeatingPlan.css";

const MIN_SEAT = 0.4;

/** Log scale: one cell holds 2,965 films and many hold one, and both must stay visible. */
function seatSize(count: number, maxCount: number) {
  return MIN_SEAT + (1 - MIN_SEAT) * (Math.log(count) / Math.log(maxCount));
}

const describeSeat = (cell: SweepCell) =>
  `${plural(cell.count, "film")}: ${plural(cell.nominations, "nomination")}, ${plural(cell.wins, "win")}`;

const seatKey = (nominations: number, wins: number) => `${nominations}:${wins}`;

interface Tip {
  cell: SweepCell;
  left: number;
  top: number;
}

interface Props {
  data: SweepData;
  step: SweepStep;
  onOpen: (cell: SweepCell) => void;
}

export function SeatingPlan({ data, step, onOpen }: Props) {
  const { maxNominations, maxWins } = data.totals;
  const planRef = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<Tip | null>(null);

  const seats = useMemo(() => new Map(data.grid.map((cell) => [seatKey(cell.nominations, cell.wins), cell])), [data.grid]);
  const maxCount = useMemo(() => Math.max(...data.grid.map((cell) => cell.count)), [data.grid]);
  const [activeKey, setActiveKey] = useState(() => seatKey(1, 0));

  const columnOf = (nominations: number) => nominations + 1;
  const rowOf = (wins: number) => maxWins - wins + 2;

  function showTip(cell: SweepCell, target: HTMLElement) {
    const plan = planRef.current?.getBoundingClientRect();
    if (!plan) return;
    const seat = target.getBoundingClientRect();
    setTip({ cell, left: seat.left - plan.left + seat.width / 2, top: seat.top - plan.top });
  }

  function moveFocus(event: KeyboardEvent<HTMLButtonElement>, cell: SweepCell) {
    const moves: Record<string, [number, number]> = {
      ArrowRight: [1, 0],
      ArrowLeft: [-1, 0],
      ArrowUp: [0, 1],
      ArrowDown: [0, -1],
    };
    const move = moves[event.key];
    if (!move) return;
    event.preventDefault();

    let { nominations, wins } = cell;
    while (true) {
      nominations += move[0];
      wins += move[1];
      if (nominations < 1 || nominations > maxNominations || wins < 0 || wins > maxWins) return;
      const key = seatKey(nominations, wins);
      if (seats.has(key)) {
        setActiveKey(key);
        planRef.current?.querySelector<HTMLButtonElement>(`[data-seat="${key}"]`)?.focus();
        return;
      }
    }
  }

  const rows = Array.from({ length: maxWins + 1 }, (_, index) => maxWins - index);
  const columns = Array.from({ length: maxNominations }, (_, index) => index + 1);

  return (
    <figure className="plan-figure">
      <figcaption className="plan-legend">
        <span className="legend-key">
          <i style={{ background: "var(--data-won)" }} /> Won at least once
        </span>
        <span className="legend-key">
          <i style={{ background: "var(--data-nominated)" }} /> Won nothing
        </span>
        <span className="legend-sizes">
          Films per seat
          {[1, 10, 100, 1000].map((count) => (
            <span className="legend-size" key={count}>
              <i style={{ "--size": seatSize(count, maxCount) } as CSSProperties} />
              {formatCount(count)}
            </span>
          ))}
        </span>
      </figcaption>

      <div className="plan" ref={planRef} onPointerLeave={() => setTip(null)}>
        <span className="plan-axis-title plan-axis-title-y">Wins</span>
        {rows.map((wins) => (
          <span key={wins} className="plan-tick" style={{ gridColumn: 1, gridRow: rowOf(wins) }}>
            {wins}
          </span>
        ))}
        {columns.map((nominations) => (
          <span key={nominations} className="plan-tick" style={{ gridColumn: columnOf(nominations), gridRow: maxWins + 3 }}>
            {nominations}
          </span>
        ))}
        <span className="plan-axis-title plan-axis-title-x" style={{ gridRow: maxWins + 4 }}>
          Nominations
        </span>

        {rows.flatMap((wins) =>
          columns.map((nominations) => {
            if (wins > nominations) return null;
            const key = seatKey(nominations, wins);
            const cell = seats.get(key);
            const place = { gridColumn: columnOf(nominations), gridRow: rowOf(wins) };

            if (!cell) return <span key={key} className="seat-empty" style={place} aria-hidden="true" />;

            const lit = step.highlight(cell);
            const className = ["seat", cell.wins > 0 ? "seat-won" : "seat-nominated", lit ? "" : "seat-dim"].join(" ");
            return (
              <button
                key={key}
                type="button"
                className={className}
                data-seat={key}
                style={{ ...place, "--size": seatSize(cell.count, maxCount) } as CSSProperties}
                tabIndex={key === activeKey ? 0 : -1}
                aria-label={describeSeat(cell)}
                onClick={() => onOpen(cell)}
                onFocus={(event) => {
                  setActiveKey(key);
                  showTip(cell, event.currentTarget);
                }}
                onBlur={() => setTip(null)}
                onPointerEnter={(event: PointerEvent<HTMLButtonElement>) => {
                  if (event.pointerType === "mouse") showTip(cell, event.currentTarget);
                }}
                onKeyDown={(event) => moveFocus(event, cell)}
              >
                <i />
              </button>
            );
          }),
        )}

        {step.labels.map((label) => (
          <span
            key={label.text}
            className={`seat-label seat-label-${label.side}`}
            style={{ gridColumn: columnOf(label.nominations), gridRow: rowOf(label.wins) }}
          >
            <span>{label.text}</span>
          </span>
        ))}

        {tip && (
          <ChartTip x={tip.left} y={tip.top} chartWidth={planRef.current?.clientWidth ?? 0} value={plural(tip.cell.count, "film")}>
            {plural(tip.cell.nominations, "nomination")}, {plural(tip.cell.wins, "win")}
          </ChartTip>
        )}
      </div>
    </figure>
  );
}
