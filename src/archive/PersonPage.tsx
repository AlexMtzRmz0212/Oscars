import { useState } from "react";
import type { PointerEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { ChartTip } from "../charts/ChartTip";
import { linearScale } from "../charts/scales";
import { useChartSize } from "../charts/useChartSize";
import { nomineeHref, shardOf } from "../lib/archive";
import type { PersonPageData } from "../lib/archive";
import { ordinal, plural } from "../lib/format";
import { useData } from "../lib/useStoryData";
import { ArchivePage, Loaded, PageHead, FullRecord, Stats } from "./parts";

const LATEST_CEREMONY = 98;
const ROW_HEIGHT = 26;
const AXIS_HEIGHT = 22;
const TICKS = [1, 25, 50, 75, 98];

interface Night {
  ceremony: number;
  year: string;
  nominated: number;
  won: number;
}

function nightsOf(person: PersonPageData): Night[] {
  const nights = new Map<number, Night>();
  for (const entry of person.entries) {
    if (entry.unofficial || !entry.competitive) continue;
    const night = nights.get(entry.ceremony) ?? { ceremony: entry.ceremony, year: entry.year, nominated: 0, won: 0 };
    night.nominated += 1;
    night.won += entry.winner ? 1 : 0;
    nights.set(entry.ceremony, night);
  }
  return [...nights.values()];
}

/** Every night of a career on one line of all 98 ceremonies, gold for a win. */
function CareerStrip({ person }: { person: PersonPageData }) {
  const { ref, width } = useChartSize({ ratio: 1, reserved: 0 });
  const [hover, setHover] = useState<Night | null>(null);
  const nights = nightsOf(person);
  if (!nights.length) return null;

  const height = ROW_HEIGHT + AXIS_HEIGHT;
  const x = linearScale([1, LATEST_CEREMONY], [6, width - 6]);
  const middle = ROW_HEIGHT / 2;

  function handleMove(event: PointerEvent<SVGRectElement>) {
    const pointerX = event.clientX - event.currentTarget.getBoundingClientRect().left;
    let best: Night | null = null;
    let bestDistance = 28;
    for (const night of nights) {
      const distance = Math.abs(x(night.ceremony) - pointerX);
      if (distance < bestDistance) {
        best = night;
        bestDistance = distance;
      }
    }
    setHover(best);
  }

  return (
    <figure className="career chart-figure">
      <figcaption className="chart-legend">
        <span>
          <i style={{ background: "var(--data-won)" }} /> Night with a win
        </span>
        <span>
          <i style={{ background: "var(--data-nominated)" }} /> Nominated only
        </span>
      </figcaption>
      <div className="chart" ref={ref}>
        {width > 0 && (
          <svg width={width} height={height} role="img" aria-label={`${plural(nights.length, "ceremony", "ceremonies")} with a nomination, from the ${ordinal(nights[0].ceremony)} to the ${ordinal(nights[nights.length - 1].ceremony)}.`}>
            <line className="chart-grid" x1={6} x2={width - 6} y1={middle} y2={middle} />
            {nights.map((night) => (
              <circle key={night.ceremony} cx={x(night.ceremony)} cy={middle} r={night.won ? 6 : 4.5} fill={night.won ? "var(--data-won)" : "var(--data-nominated)"} stroke="var(--velvet-black)" strokeWidth={2} />
            ))}
            {TICKS.map((tick) => (
              <text key={tick} className="chart-text" x={x(tick)} y={height - 5} textAnchor={tick === 1 ? "start" : tick === LATEST_CEREMONY ? "end" : "middle"}>
                {ordinal(tick)}
              </text>
            ))}
            <rect x={0} y={0} width={width} height={height} fill="transparent" onPointerMove={handleMove} onPointerLeave={() => setHover(null)} />
          </svg>
        )}
        {hover && (
          <ChartTip x={x(hover.ceremony)} y={4} chartWidth={width} value={`${ordinal(hover.ceremony)} ceremony`}>
            {plural(hover.nominated, "nomination")}, {plural(hover.won, "win")}
          </ChartTip>
        )}
      </div>
    </figure>
  );
}

export default function PersonPage() {
  const { id = "" } = useParams();
  const state = useData<Record<string, PersonPageData>>(`people/${shardOf(id)}`);

  return (
    <Loaded state={state} missing="Nobody in the record has that id.">
      {(shard) => {
        const person = shard[id];
        if (!person) return <Loaded state={{ status: "error" }} missing="Nobody in the record has that id.">{() => null}</Loaded>;
        const stats: [string, string][] = [
          [String(person.nominations), person.nominations === 1 ? "nomination" : "nominations"],
          [String(person.wins), person.wins === 1 ? "win" : "wins"],
        ];
        if (person.honors) stats.push([String(person.honors), person.honors === 1 ? "honor" : "honors"]);

        return (
          <ArchivePage title={person.name}>
            <PageHead title={person.name}>
              {person.birthYear && <p>Born {person.birthYear}</p>}
              {person.type === "company" && <p>A studio or company credited directly by the Academy.</p>}
              {person.type === "unknown" && <p>The record names this credit without a linked identity, so it may share a page with a namesake or split across spellings.</p>}
              <Stats items={stats} />
            </PageHead>
            <CareerStrip person={person} />
            {person.partners.length > 0 && (
              <div className="sheet">
                <h2>Often credited with</h2>
                <ul className="partners">
                  {person.partners.map((partner) => (
                    <li key={partner.id}>
                      <Link to={nomineeHref(partner)}>{partner.name}</Link> ({partner.shared})
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <FullRecord entries={person.entries} skipId={person.id} />
          </ArchivePage>
        );
      }}
    </Loaded>
  );
}
