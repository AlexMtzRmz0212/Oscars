import { useMemo, useState } from "react";
import type { PointerEvent } from "react";
import { ChartTip } from "../../charts/ChartTip";
import { DataTableToggle } from "../../charts/DataTableToggle";
import { linearScale, logScale } from "../../charts/scales";
import { useChartSize } from "../../charts/useChartSize";
import { formatCount, formatDollars } from "../../lib/format";
import type { MoneyData, MoneyNominee } from "../../lib/types";
import { Act } from "../Act";
import { ScrollStory } from "../ScrollStory";
import type { StorySlip } from "../ScrollStory";
import "./acts.css";

interface MoneyStep extends StorySlip {
  range?: [number, number];
  medians?: boolean;
  topGrossers?: boolean;
}

const Y_TICKS = [1e6, 1e8, 1e10];
const X_TICKS = [1930, 1950, 1970, 1990, 2010];
const Y_DOMAIN: [number, number] = [1e5, 1.5e10];
const MARGIN = { left: 48, right: 8, top: 8, bottom: 24 };
/** Far enough to count as pointing at nothing. */
const HIT_RADIUS = 40;

function MoneyScatter({ data, step }: { data: MoneyData; step: MoneyStep }) {
  const { ref, width, height } = useChartSize({ ratio: 0.66, pinnedShare: 0.42 });
  const [hover, setHover] = useState<MoneyNominee | null>(null);

  const x = linearScale([1927, 2026], [MARGIN.left, width - MARGIN.right]);
  const y = logScale(Y_DOMAIN, [height - MARGIN.bottom, MARGIN.top]);
  const dotSmall = width < 520 ? 2 : 3;
  const dotWinner = width < 520 ? 3.5 : 5;

  const inRange = (nominee: MoneyNominee) => !step.range || (nominee.year >= step.range[0] && nominee.year <= step.range[1]);

  // Winners draw last so they stay on top of the crowd.
  const ordered = useMemo(() => [...data.nominees].sort((a, b) => Number(a.winner) - Number(b.winner)), [data.nominees]);

  const medianPath = data.decades
    .filter((decade) => decade.medianWinner !== null)
    .map((decade) => {
      const start = Math.max(decade.decade, 1927);
      const end = Math.min(decade.decade + 10, 2026);
      return `M${x(start)},${y(decade.medianWinner as number)}H${x(end)}`;
    })
    .join("");

  function handleMove(event: PointerEvent<SVGRectElement>) {
    // Measured from the chart, not this hit area, which starts after the axis margin.
    const box = (event.currentTarget.ownerSVGElement ?? event.currentTarget).getBoundingClientRect();
    const pointerX = event.clientX - box.left;
    const pointerY = event.clientY - box.top;
    let best: MoneyNominee | null = null;
    let bestDistance = HIT_RADIUS;
    for (const nominee of data.nominees) {
      const distance = Math.hypot(x(nominee.year) - pointerX, y(nominee.revenue) - pointerY);
      if (distance < bestDistance) {
        best = nominee;
        bestDistance = distance;
      }
    }
    setHover(best);
  }

  return (
    <figure className="chart-figure">
      <figcaption className="chart-legend">
        <span>
          <i style={{ background: "var(--data-won)" }} /> Won Best Picture
        </span>
        <span>
          <i style={{ background: "var(--data-nominated)" }} /> Other nominee
        </span>
        {step.medians && (
          <span>
            <i style={{ background: "var(--ivory)", height: 2, width: 18, borderRadius: 0 }} /> Decade’s median winner
          </span>
        )}
        {step.topGrossers && (
          <span>
            <i style={{ background: "transparent", boxShadow: "inset 0 0 0 2px var(--ivory)" }} /> Top grosser that night
          </span>
        )}
      </figcaption>
      <div className="chart" ref={ref}>
        {width > 0 && (
          <svg width={width} height={height} role="img" aria-label="Lifetime gross of each Best Picture nominee by film year, in 2025 dollars, on a logarithmic scale.">
            {Y_TICKS.map((tick) => (
              <g key={tick}>
                <line className="chart-grid" x1={MARGIN.left} x2={width - MARGIN.right} y1={y(tick)} y2={y(tick)} />
                <text className="chart-text" x={MARGIN.left - 6} y={y(tick) + 4} textAnchor="end">
                  {formatDollars(tick)}
                </text>
              </g>
            ))}
            {X_TICKS.map((tick) => (
              <text key={tick} className="chart-text" x={x(tick)} y={height - 6} textAnchor="middle">
                {tick}
              </text>
            ))}

            {ordered.map((nominee) => {
              const lit = inRange(nominee);
              const ring = step.topGrossers && nominee.topGrosser && lit;
              return (
                <circle
                  key={`${nominee.ceremony}-${nominee.title}`}
                  cx={x(nominee.year)}
                  cy={y(nominee.revenue)}
                  r={ring ? dotWinner + 1 : nominee.winner ? dotWinner : dotSmall}
                  fill={ring && !nominee.winner ? "var(--velvet-black)" : nominee.winner ? "var(--data-won)" : "var(--data-nominated)"}
                  stroke={ring ? "var(--ivory)" : "var(--velvet-black)"}
                  strokeWidth={ring ? 2 : nominee.winner ? 2 : 0}
                  opacity={lit ? 1 : 0.16}
                  style={{ transition: "opacity 360ms ease" }}
                />
              );
            })}

            {step.medians && <path d={medianPath} fill="none" stroke="var(--ivory)" strokeWidth={2} strokeLinecap="round" />}

            {hover && <circle cx={x(hover.year)} cy={y(hover.revenue)} r={dotWinner + 3} fill="none" stroke="var(--gold-bright)" strokeWidth={2} />}
            <rect
              x={MARGIN.left}
              y={0}
              width={width - MARGIN.left}
              height={height}
              fill="transparent"
              onPointerMove={handleMove}
              onPointerLeave={() => setHover(null)}
            />
          </svg>
        )}
        {hover && (
          <ChartTip x={x(hover.year)} y={y(hover.revenue)} chartWidth={width} value={formatDollars(hover.revenue)}>
            {hover.title} ({hover.year}){hover.winner ? ", winner" : ""}
          </ChartTip>
        )}
      </div>
    </figure>
  );
}

function buildSteps({ nominees, decades, topGrosser }: MoneyData): MoneyStep[] {
  const median = (decade: number) => formatDollars(decades.find((row) => row.decade === decade)?.medianWinner ?? 0);
  const total = decades.reduce((sum, row) => sum + row.nominees, 0);

  return [
    {
      id: "all",
      heading: "What the nominees earned",
      body: `Each dot is a nominee’s lifetime gross in 2025 dollars, for the ${formatCount(nominees.length)} of ${formatCount(total)} with revenue on TMDb. Re-releases inflate old totals and some old entries look too low, so compare eras, not single old films.`,
    },
    {
      id: "hits",
      heading: "Winners used to be hits",
      body: `The median Best Picture winner earned ${median(1990)} in the 1990s and ${median(2000)} in the 2000s. The top-grossing nominee won ${topGrosser["1990to2009"].won} of ${topGrosser["1990to2009"].ceremonies} times.`,
      range: [1990, 2009],
      medians: true,
    },
    {
      id: "twenty-tens",
      heading: "The 2010s broke the link",
      body: `The median winner fell to ${median(2010)}, and that was before the pandemic closed theaters. Across all ${topGrosser["2010s"].ceremonies} ceremonies, the top-grossing nominee won ${topGrosser["2010s"].won} times.`,
      range: [2010, 2019],
      medians: true,
      topGrossers: true,
    },
    {
      id: "since",
      heading: `Since 2020 the median is ${median(2020)}`,
      body: "The pandemic closed theaters and streaming films report little or no box office, so this drop overstates the shift. CODA won with about $2M.",
      range: [2020, 2025],
      medians: true,
    },
  ];
}

export function TheMoney() {
  return (
    <Act<MoneyData>
      id="the-money"
      title="Act IV: The Money"
      note="For decades the biggest prize often went to a film people had already paid to see. That link has come apart."
      field="velvet"
      dataName="money"
      facts={({ decades, topGrosser }) => {
        const median = (decade: number) => formatDollars(decades.find((row) => row.decade === decade)?.medianWinner ?? 0);
        return [
          [median(1990), "median winner, 1990s"],
          [median(2010), "median winner, 2010s"],
          [`${topGrosser["2010s"].won} of ${topGrosser["2010s"].ceremonies}`, "top grossers won in the 2010s"],
        ];
      }}
    >
      {(data) => (
        <>
          <ScrollStory slips={buildSteps(data)} renderStage={(step) => <MoneyScatter data={data} step={step} />} />
          <div className="act-table">
            <DataTableToggle
              summary="Read this chart as a table"
              headers={["Decade", "Median winner, 2025 dollars", "Winners with revenue", "Nominees with revenue"]}
              rows={data.decades.map((decade) => [
                `${decade.decade}s`,
                decade.medianWinner === null ? "Unknown" : formatDollars(decade.medianWinner),
                `${decade.winnersKnown} of ${decade.winners}`,
                `${decade.nomineesKnown} of ${decade.nominees}`,
              ])}
            />
          </div>
        </>
      )}
    </Act>
  );
}
