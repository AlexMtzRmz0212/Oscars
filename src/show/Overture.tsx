import { motion, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import type { PointerEvent } from "react";
import { Link } from "react-router-dom";
import { ChartTip } from "../charts/ChartTip";
import { DataTableToggle } from "../charts/DataTableToggle";
import { useChartSize } from "../charts/useChartSize";
import { formatCount, plural } from "../lib/format";
import { rise, riseAfter } from "../lib/motion";
import type { OvertureData } from "../lib/types";
import { useStoryData } from "../lib/useStoryData";
import "./Overture.css";

const REVEAL_MS = 1400;
const AXIS_YEARS = [1, 25, 50, 75, 98];

const PROGRAMME = [
  ["#the-programme", "Act I: The Programme", "How has the show changed?"],
  ["#the-sweep", "Act II: The Sweep", "What does dominance look like?"],
  ["#the-formula", "Act III: The Formula", "What travels with Best Picture?"],
  ["#the-money", "Act IV: The Money", "Has the Academy left the box office behind?"],
  ["#the-audience", "Act V: The Audience Votes", "Does the audience’s favorite win?"],
  ["#the-gold", "Act VI: Who Gets the Gold", "Who gets recognized, and at what age?"],
  ["#snubbed", "Act VII: Snubbed", "Who keeps coming so close?"],
  ["#encore", "Encore", "What won the year you were born?"],
];
const AFTER_SHOW = ["/season", "The 99th", "Who wins next, and how far to trust that?"];

/** One dot per competitive nomination, stacked in its ceremony's column, gold if it won. */
function PointsOfLight({ columns }: { columns: OvertureData["columns"] }) {
  const reduced = useReducedMotion();
  const { ref, width, height } = useChartSize({ ratio: 0.34, pinnedShare: 0.45, reserved: 340 });
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [progress, setProgress] = useState(reduced ? 1 : 0);
  const [hover, setHover] = useState<{ index: number; x: number } | null>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element || reduced) return;
    let frame = 0;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        const start = performance.now();
        const tick = (now: number) => {
          const next = Math.min((now - start) / REVEAL_MS, 1);
          setProgress(next);
          if (next < 1) frame = requestAnimationFrame(tick);
        };
        frame = requestAnimationFrame(tick);
      },
      { threshold: 0.25 },
    );
    observer.observe(element);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [ref, reduced]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context || width === 0) return;

    const ratio = window.devicePixelRatio || 1;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);

    const styles = getComputedStyle(canvas);
    const gold = styles.getPropertyValue("--data-won").trim();
    const ivory = styles.getPropertyValue("--data-nominated").trim();

    const band = width / columns.length;
    const tallest = Math.max(...columns.map((column) => column.nominations));
    const pitch = Math.sqrt((height * band) / tallest);
    const perRow = Math.max(1, Math.round(band / pitch));
    const rowHeight = height / Math.ceil(tallest / perRow);
    const across = band / perRow;
    const dot = Math.max(1, Math.min(across, rowHeight) * 0.62);
    const litColumns = progress * columns.length;

    columns.forEach((column, columnIndex) => {
      if (columnIndex > litColumns) return;
      for (let index = 0; index < column.nominations; index += 1) {
        const x = columnIndex * band + (index % perRow) * across;
        const y = height - (Math.floor(index / perRow) + 1) * rowHeight;
        // Winners spread evenly up the column, so the gold reads as light rather than a floor.
        const isWinner = Math.floor(((index + 1) * column.wins) / column.nominations) > Math.floor((index * column.wins) / column.nominations);
        context.fillStyle = isWinner ? gold : ivory;
        context.fillRect(x, y, dot, dot);
      }
    });
  }, [columns, width, height, progress]);

  function handleMove(event: PointerEvent<HTMLDivElement>) {
    const x = event.clientX - event.currentTarget.getBoundingClientRect().left;
    const index = Math.floor((x / width) * columns.length);
    if (index >= 0 && index < columns.length) setHover({ index, x });
  }

  const hovered = hover && columns[hover.index];

  return (
    <div
      className="chart lights"
      ref={ref}
      onPointerMove={handleMove}
      onPointerLeave={() => setHover(null)}
    >
      <canvas
        ref={canvasRef}
        role="img"
        aria-label={`Dots for every competitive nomination, in a column for each ceremony, from ${columns[0].nominations} at the first ceremony to ${columns[columns.length - 1].nominations} at the latest.`}
        style={{ width, height, display: "block" }}
      />
      <div className="lights-axis" aria-hidden="true">
        {AXIS_YEARS.map((ceremony) => (
          <span key={ceremony} style={{ left: `${((ceremony - 0.5) / columns.length) * 100}%` }}>
            {columns[ceremony - 1]?.year.split("/")[0]}
          </span>
        ))}
      </div>
      {hover && hovered && (
        <ChartTip x={hover.x} y={height * 0.4} chartWidth={width} value={plural(hovered.nominations, "nomination")}>
          {plural(hovered.wins, "winner")} at ceremony {hovered.ceremony}, films of {hovered.year}
        </ChartTip>
      )}
    </div>
  );
}

export function Overture() {
  const overture = useStoryData<OvertureData>("overture");

  return (
    <section className="overture" id="overture" aria-labelledby="overture-title">
      <div className="overture-head">
        <motion.h2 id="overture-title" {...rise}>
          Overture
        </motion.h2>
        {overture.status === "ready" && (
          <motion.p className="overture-statement" {...riseAfter(1)}>
            {overture.data.columns.length} ceremonies and {formatCount(overture.data.totals.nominations)} competitive
            nominations. Each one is a point of light, and the {formatCount(overture.data.totals.wins)} in gold won.
          </motion.p>
        )}
      </div>

      {overture.status === "error" && (
        <p role="alert">The house lights didn’t load. Refresh the page to try again.</p>
      )}
      {overture.status === "ready" && (
        <>
          <div className="chart-legend">
            <span>
              <i style={{ background: "var(--data-won)", borderRadius: 2 }} /> Won
            </span>
            <span>
              <i style={{ background: "var(--data-nominated)", borderRadius: 2 }} /> Nominated
            </span>
          </div>
          <PointsOfLight columns={overture.data.columns} />
          <div className="act-table">
            <DataTableToggle
              summary="Read this chart as a table"
              headers={["Ceremony", "Films of", "Nominations", "Winners"]}
              rows={overture.data.columns.map((column) => [column.ceremony, column.year, column.nominations, column.wins])}
            />
          </div>
        </>
      )}

      <motion.nav className="programme-sheet" aria-label="Tonight’s programme" {...rise}>
        <h3>Tonight’s programme</h3>
        <ol>
          {PROGRAMME.map(([href, title, question]) => (
            <li key={href}>
              <a href={href}>
                <span className="programme-title">{title}</span>
                <span className="programme-question">{question}</span>
              </a>
            </li>
          ))}
          <li>
            <Link to={AFTER_SHOW[0]}>
              <span className="programme-title">{AFTER_SHOW[1]}</span>
              <span className="programme-question">{AFTER_SHOW[2]}</span>
            </Link>
          </li>
        </ol>
      </motion.nav>
    </section>
  );
}
