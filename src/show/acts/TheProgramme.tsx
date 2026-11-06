import { useMemo, useState } from "react";
import type { PointerEvent } from "react";
import { ChartTip } from "../../charts/ChartTip";
import { DataTableToggle } from "../../charts/DataTableToggle";
import { linearScale } from "../../charts/scales";
import { useChartSize } from "../../charts/useChartSize";
import { ordinal, plural } from "../../lib/format";
import type { ProgrammeData } from "../../lib/types";
import { Act } from "../Act";
import { ScrollStory } from "../ScrollStory";
import type { StorySlip } from "../ScrollStory";
import "./acts.css";

interface ProgrammeStep extends StorySlip {
  ceremony?: number;
  family?: string;
}

const SPARK_HEIGHT = 56;
const AXIS_HEIGHT = 26;
const TICKS = [1, 25, 50, 75, 98];
const COUNT_FILLS = ["transparent", "var(--data-count-1)", "var(--data-count-2)", "var(--data-count-3)"];

const fillFor = (count: number) => COUNT_FILLS[Math.min(count, COUNT_FILLS.length - 1)];

/** Runs of consecutive nights with the same number of categories, so each draws as one rectangle. */
function toRuns(counts: number[]) {
  const runs: { start: number; length: number; count: number }[] = [];
  counts.forEach((count, index) => {
    const last = runs[runs.length - 1];
    if (last && last.count === count) last.length += 1;
    else runs.push({ start: index, length: 1, count });
  });
  return runs.filter((run) => run.count > 0);
}

function ProgrammeStrip({ data, step }: { data: ProgrammeData; step: ProgrammeStep }) {
  const { ref, width, height } = useChartSize({ ratio: 0.8, pinnedShare: 0.44 });
  const [hover, setHover] = useState<number | null>(null);

  const labelWidth = width < 520 ? 96 : 124;
  const x = linearScale([0, data.ceremonies.length], [labelWidth, width - 4]);
  const band = x(1) - x(0);
  const rowsTop = SPARK_HEIGHT + 6;
  const rowHeight = (height - rowsTop - AXIS_HEIGHT) / data.families.length;
  const spark = linearScale([0, data.facts.peak], [SPARK_HEIGHT - 2, 14]);
  const runs = useMemo(() => data.families.map((family) => toRuns(family.counts)), [data.families]);

  const sparkPath = data.ceremonies
    .map((ceremony, index) => `${index === 0 ? "M" : "L"}${x(index)},${spark(ceremony.total)}H${x(index + 1)}`)
    .join("");

  function handleMove(event: PointerEvent<SVGRectElement>) {
    const left = event.currentTarget.getBoundingClientRect().left;
    const index = Math.floor((event.clientX - left) / band);
    setHover(index >= 0 && index < data.ceremonies.length ? index : null);
  }

  const hovered = hover === null ? null : data.ceremonies[hover];
  const focusIndex = step.ceremony ? step.ceremony - 1 : null;

  return (
    <figure className="chart-figure">
      <figcaption className="chart-legend">
        <span>Categories in that family that night:</span>
        {[1, 2, 3].map((count) => (
          <span key={count}>
            <i style={{ background: fillFor(count), borderRadius: 2 }} /> {count === 3 ? "3 or more" : count}
          </span>
        ))}
      </figcaption>
      <div className="chart" ref={ref}>
        {width > 0 && (
          <svg
            width={width}
            height={height}
            role="img"
            aria-label={`Categories per ceremony, by family. ${data.facts.first} at the first ceremony, ${data.facts.peak} at the ${ordinal(data.facts.peakCeremony)}, ${data.facts.latest} today.`}
          >
            {focusIndex !== null && (
              <rect x={x(focusIndex)} y={0} width={Math.max(band, 3)} height={height - AXIS_HEIGHT} fill="var(--data-empty)" />
            )}

            <path d={sparkPath} fill="none" stroke="var(--ivory)" strokeWidth={2} strokeLinejoin="round" />
            <text className="chart-text chart-text-strong" x={x(0)} y={spark(data.facts.first) - 6}>
              {data.facts.first}
            </text>
            <text className="chart-text chart-text-strong" x={x(data.facts.peakCeremony - 1)} y={10} textAnchor="middle">
              {data.facts.peak}
            </text>
            <text className="chart-text chart-text-strong" x={width - 4} y={spark(data.facts.latest) - 6} textAnchor="end">
              {data.facts.latest}
            </text>
            <text className="chart-text" x={labelWidth - 8} y={SPARK_HEIGHT - 6} textAnchor="end">
              All categories
            </text>

            {data.families.map((family, rowIndex) => {
              const y = rowsTop + rowIndex * rowHeight;
              const dim = (step.family && step.family !== family.name) || (focusIndex !== null && !step.family);
              return (
                <g key={family.name}>
                  <text className="chart-text" x={labelWidth - 8} y={y + rowHeight / 2 + 4} textAnchor="end" fill={step.family === family.name ? "var(--ivory)" : undefined}>
                    {family.name}
                  </text>
                  <g opacity={dim ? 0.28 : 1} style={{ transition: "opacity 360ms ease" }}>
                    {runs[rowIndex].map((run) => (
                      <rect
                        key={run.start}
                        x={x(run.start)}
                        y={y + 1}
                        width={Math.max(band * run.length, 2.5)}
                        height={Math.max(rowHeight - 2, 3)}
                        fill={fillFor(run.count)}
                      />
                    ))}
                  </g>
                  {focusIndex !== null && family.counts[focusIndex] > 0 && !step.family && (
                    <rect x={x(focusIndex)} y={y + 1} width={Math.max(band, 3)} height={Math.max(rowHeight - 2, 3)} fill={fillFor(family.counts[focusIndex])} />
                  )}
                </g>
              );
            })}

            {TICKS.map((ceremony) => (
              <text
                key={ceremony}
                className="chart-text"
                x={x(ceremony - 0.5)}
                y={height - 6}
                textAnchor={ceremony === 1 ? "start" : ceremony === 98 ? "end" : "middle"}
              >
                {data.ceremonies[ceremony - 1].year.split("/")[0]}
              </text>
            ))}

            {hover !== null && <line x1={x(hover + 0.5)} x2={x(hover + 0.5)} y1={0} y2={height - AXIS_HEIGHT} stroke="var(--muted)" />}
            <rect
              x={labelWidth}
              y={0}
              width={width - labelWidth}
              height={height}
              fill="transparent"
              onPointerMove={handleMove}
              onPointerLeave={() => setHover(null)}
            />
          </svg>
        )}
        {hover !== null && hovered && (
          <ChartTip x={x(hover + 0.5)} y={20} chartWidth={width} value={plural(hovered.total, "category", "categories")}>
            Ceremony {hovered.ceremony}, films of {hovered.year}
          </ChartTip>
        )}
      </div>
    </figure>
  );
}

function buildSteps({ facts }: ProgrammeData): ProgrammeStep[] {
  return [
    {
      id: "first",
      heading: `The first night had ${facts.first} categories`,
      body: "The first ceremony honored films of 1927 and 1928. It gave separate directing awards for comedy and drama, and one prize for title writing.",
      ceremony: 1,
    },
    {
      id: "peak",
      heading: `By ${facts.peakYear} there were ${facts.peak}`,
      body: `At the ${ordinal(facts.peakCeremony)} ceremony, cinematography, art direction and costume design each had separate black-and-white and color prizes, and that counts as two categories each.`,
      ceremony: facts.peakCeremony,
    },
    {
      id: "retired",
      heading: "Nearly half are gone",
      body: `The Academy has fielded ${facts.everCategories} categories, and ${facts.retired} have been retired or merged. Title Writing lasted one night and Dance Direction lasted three.`,
    },
    {
      id: "casting",
      heading: "Casting is the newest",
      body: `Casting joined at the 98th ceremony, the first new category since Animated Feature at the 74th. The night now has ${facts.latest}.`,
      family: "Casting",
    },
  ];
}

export function TheProgramme() {
  return (
    <Act<ProgrammeData>
      id="the-programme"
      title="Act I: The Programme"
      note="The show keeps rewriting itself. Before asking who won, it helps to see what there was to win, night by night, for 98 ceremonies."
      field="oxblood"
      dataName="programme"
    >
      {(data) => (
        <>
          <ScrollStory slips={buildSteps(data)} renderStage={(step) => <ProgrammeStrip data={data} step={step} />} />
          <div className="act-table">
            <DataTableToggle
              summary="Read this chart as a table"
              headers={["Ceremony", "Films of", "Categories"]}
              rows={data.ceremonies.map((ceremony) => [ceremony.ceremony, ceremony.year, ceremony.total])}
            />
          </div>
        </>
      )}
    </Act>
  );
}
