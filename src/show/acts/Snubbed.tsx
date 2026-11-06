import { motion } from "motion/react";
import { Link } from "react-router-dom";
import { filmHref } from "../../lib/archive";
import { DataTableToggle } from "../../charts/DataTableToggle";
import { linearScale } from "../../charts/scales";
import { useChartSize } from "../../charts/useChartSize";
import { ordinal } from "../../lib/format";
import { riseAfter, rise } from "../../lib/motion";
import { Poster } from "../../components/Poster";
import type { SnubbedData } from "../../lib/types";
import { Act } from "../Act";
import { ScrollStory } from "../ScrollStory";
import type { StorySlip } from "../ScrollStory";
import "./acts.css";

interface SnubbedStep extends StorySlip {
  focus: string[];
}

const MARGIN = { left: 30, right: 10, top: 16, bottom: 24 };
const X_TICKS = [50, 60, 70, 80, 90, 98];
const LABEL_CEREMONY: Record<string, number> = { nm0002353: 84 };

function CareerLines({ data, step }: { data: SnubbedData; step: SnubbedStep }) {
  const { ref, width, height } = useChartSize({ ratio: 0.66, pinnedShare: 0.42 });
  const most = Math.max(...data.careers.map((career) => career.nominations));
  const first = Math.min(...data.careers.flatMap((career) => career.points.map((point) => point.ceremony)));

  const x = linearScale([first, 98], [MARGIN.left, width - MARGIN.right]);
  const y = linearScale([0, most], [height - MARGIN.bottom, MARGIN.top]);
  const yTicks = [0, 20, 40];

  return (
    <figure className="chart-figure">
      <figcaption className="chart-legend">
        <span>Career nominations, with a gold dot for each night of a win</span>
      </figcaption>
      <div className="chart" ref={ref}>
        {width > 0 && (
          <svg width={width} height={height} role="img" aria-label={data.careers.map((career) => `${career.name}: ${career.nominations} nominations, ${career.wins} wins`).join(". ")}>
            {yTicks.map((tick) => (
              <g key={tick}>
                <line className="chart-grid" x1={MARGIN.left} x2={width - MARGIN.right} y1={y(tick)} y2={y(tick)} />
                <text className="chart-text" x={MARGIN.left - 6} y={y(tick) + 4} textAnchor="end">
                  {tick}
                </text>
              </g>
            ))}
            {X_TICKS.filter((tick) => tick >= first).map((tick) => (
              <text key={tick} className="chart-text" x={x(tick)} y={height - 6} textAnchor={tick === 98 ? "end" : "middle"}>
                {ordinal(tick)}
              </text>
            ))}

            {data.careers.map((career) => {
              const lit = step.focus.includes(career.id);
              const path = career.points
                .map((point, index) => `${index === 0 ? `M${x(point.ceremony)},${y(0)}` : `H${x(point.ceremony)}`}V${y(point.nominations)}`)
                .join("");
              const last = career.points[career.points.length - 1];
              // Two careers finish level, so a label can sit further back along its own line.
              const labelCeremony = LABEL_CEREMONY[career.id] ?? 98;
              const labelPoint = [...career.points].reverse().find((point) => point.ceremony <= labelCeremony) ?? last;
              return (
                <g key={career.id} opacity={lit ? 1 : 0.3} style={{ transition: "opacity 360ms ease" }}>
                  <path d={`${path}H${x(98)}`} fill="none" stroke={lit ? "var(--ivory)" : "var(--data-nominated)"} strokeWidth={2} strokeLinejoin="round" />
                  {career.points
                    .filter((point) => point.wins > 0)
                    .map((point) => (
                      <circle key={point.ceremony} cx={x(point.ceremony)} cy={y(point.nominations)} r={5} fill="var(--data-won)" stroke="var(--velvet-black)" strokeWidth={2} />
                    ))}
                  <text className="chart-text chart-text-strong" x={x(labelCeremony)} y={y(labelPoint.nominations) - 8} textAnchor="end">
                    {career.name}, {career.wins} for {career.nominations}
                  </text>
                </g>
              );
            })}
          </svg>
        )}
      </div>
    </figure>
  );
}

function buildSteps({ careers }: SnubbedData): SnubbedStep[] {
  const [williams, warren, newman] = careers;
  return [
    {
      id: "williams",
      heading: "Even the greats mostly lose",
      body: `${williams.name} has ${williams.nominations} nominations, more than any other living person, and ${williams.wins} wins. More than nine times in ten, the name in the envelope was someone else’s.`,
      focus: [williams.id],
    },
    {
      id: "warren",
      heading: `${warren.name} is 0 for ${warren.nominations}`,
      body: "The longest competitive losing record of anyone, across more than three decades of original songs. The one Oscar on the shelf is an honorary award.",
      focus: [warren.id],
    },
    {
      id: "newman",
      heading: `${newman.name} is 0 for ${newman.nominations}`,
      body: "Fifteen nominations for score and song since the 1990s, and no win. Only a handful of people have been nominated this often and never won.",
      focus: [newman.id, warren.id],
    },
  ];
}

function Leaderboards({ data }: { data: SnubbedData }) {
  return (
    <div className="board">
      <motion.h3 {...rise}>Most nominations, nothing to show</motion.h3>
      <ul className="board-films">
        {data.films.map(
          (film, index) =>
            film.poster && (
              <motion.li key={film.id} {...riseAfter(index)}>
                <Link to={filmHref(film.id)}>
                  <Poster path={film.poster} alt="" sizes="(max-width: 900px) 24vw, 12vw" />
                  <span className="board-score">0 for {film.nominations}</span>
                  <span className="board-name">{film.title}</span>
                </Link>
              </motion.li>
            ),
        )}
      </ul>
      <ul className="board-people">
        {data.people.map((person) => (
          <li key={person.name}>
            <span className="board-score">0 for {person.nominations}</span>
            <span>
              <Link to={`/people/${person.id}`}>{person.name}</Link>
              {person.honors > 0 ? ", with a non-competitive honor" : ""}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Snubbed() {
  return (
    <Act<SnubbedData>
      id="snubbed"
      title="Act VII: Snubbed"
      note="A nomination is the show’s consolation prize, and some of its most familiar names have collected nothing else."
      field="curtain"
      dataName="snubbed"
      facts={({ films, people }) => [
        [`0 for ${films[0].nominations}`, `${films[0].title} and ${films[1].title}`],
        [`0 for ${people[0].nominations}`, `${people[0].name}, competitively`],
      ]}
    >
      {(data) => (
        <>
          <ScrollStory slips={buildSteps(data)} renderStage={(step) => <CareerLines data={data} step={step} />} />
          <div className="act-table">
            <DataTableToggle
              summary="Read this chart as a table"
              headers={["Name", "Nominations", "Wins"]}
              rows={data.careers.map((career) => [<Link to={`/people/${career.id}`}>{career.name}</Link>, career.nominations, career.wins])}
            />
          </div>
          <Leaderboards data={data} />
        </>
      )}
    </Act>
  );
}
