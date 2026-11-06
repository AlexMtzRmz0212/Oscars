import { motion } from "motion/react";
import { useMemo, useState } from "react";
import type { PointerEvent } from "react";
import { Link } from "react-router-dom";
import { ChartTip } from "../../charts/ChartTip";
import { DataTableToggle } from "../../charts/DataTableToggle";
import { linearScale } from "../../charts/scales";
import { useChartSize } from "../../charts/useChartSize";
import { filmHref } from "../../lib/archive";
import { formatPercent, joinNames, ordinal } from "../../lib/format";
import { rise, riseAfter } from "../../lib/motion";
import { Poster } from "../../components/Poster";
import type { AgeGroup, AgeWinner, GoldData } from "../../lib/types";
import { Act } from "../Act";
import { ScrollStory } from "../ScrollStory";
import type { StorySlip } from "../ScrollStory";
import "./acts.css";

const AGE_DOMAIN: [number, number] = [20, 85];
const AGE_TICKS = [20, 30, 40, 50, 60, 70, 80];
const AXIS_ROOM = 22;
const HIT_RADIUS = 28;
/** Empty space between the two groups, so each reads as its own. */
const GROUP_GAP = 7;
const LABEL_ROOM = 24;

interface PlacedWinner extends AgeWinner {
  x: number;
  y: number;
}

/** Stacks winners of the same age into a column, growing away from the middle line. */
function placeWinners(group: AgeGroup, x: (age: number) => number, middle: number, step: number) {
  const seen = new Map<number, number>();
  return group.winners.map((winner): PlacedWinner => {
    const count = seen.get(winner.age) ?? 0;
    seen.set(winner.age, count + 1);
    return { ...winner, x: x(winner.age), y: middle + step * (count + 0.5) };
  });
}

function AgeChart({ data }: { data: GoldData }) {
  const { ref, width, height } = useChartSize({ ratio: 0.52, pinnedShare: 0.42 });
  const [hover, setHover] = useState<PlacedWinner | null>(null);

  const x = linearScale(AGE_DOMAIN, [8, width - 8]);
  const middle = (height - AXIS_ROOM) / 2;
  const reach = middle - GROUP_GAP - LABEL_ROOM;
  const { actor, actress } = data.ages;

  const tallest = useMemo(() => {
    let highest = 0;
    for (const group of [actor, actress]) {
      const groupCounts = new Map<number, number>();
      for (const winner of group.winners) {
        const next = (groupCounts.get(winner.age) ?? 0) + 1;
        groupCounts.set(winner.age, next);
        highest = Math.max(highest, next);
      }
    }
    return highest;
  }, [actor, actress]);

  const bandWidth = x(21) - x(20);
  const pitch = Math.min(bandWidth, reach / Math.max(tallest, 1));
  const radius = Math.max(pitch / 2 - 0.5, 1.5);

  const men = placeWinners(actor, x, middle - GROUP_GAP, -pitch);
  const women = placeWinners(actress, x, middle + GROUP_GAP, pitch);
  const everyone = [...men, ...women];

  function handleMove(event: PointerEvent<SVGRectElement>) {
    const box = event.currentTarget.getBoundingClientRect();
    const pointerX = event.clientX - box.left;
    const pointerY = event.clientY - box.top;
    let best: PlacedWinner | null = null;
    let bestDistance = HIT_RADIUS;
    for (const winner of everyone) {
      const distance = Math.hypot(winner.x - pointerX, winner.y - pointerY);
      if (distance < bestDistance) {
        best = winner;
        bestDistance = distance;
      }
    }
    setHover(best);
  }

  return (
    <figure className="chart-figure">
      <div className="chart" ref={ref}>
        {width > 0 && (
          <svg width={width} height={height} role="img" aria-label={`Age of every lead acting winner. Best Actor median ${actor.median}, Best Actress median ${actress.median}.`}>
            <text className="chart-text chart-text-strong" x={width - 8} y={18} textAnchor="end">
              Best Actor, median {actor.median}
            </text>
            <text className="chart-text chart-text-strong" x={width - 8} y={height - AXIS_ROOM - 8} textAnchor="end">
              Best Actress, median {actress.median}
            </text>
            <line className="chart-grid" x1={8} x2={width - 8} y1={middle} y2={middle} />

            {[...men, ...women].map((winner) => (
              <circle key={`${winner.name}-${winner.year}`} cx={winner.x} cy={winner.y} r={radius} fill="var(--data-won)" />
            ))}

            {[
              { value: actor.median, from: middle - GROUP_GAP, to: middle - GROUP_GAP - pitch * tallest },
              { value: actress.median, from: middle + GROUP_GAP, to: middle + GROUP_GAP + pitch * tallest },
            ].map((mark) => (
              <line key={mark.to} x1={x(mark.value)} x2={x(mark.value)} y1={mark.from} y2={mark.to} stroke="var(--ivory)" strokeWidth={2} />
            ))}

            {AGE_TICKS.map((tick) => (
              <text key={tick} className="chart-text" x={x(tick)} y={height - 6} textAnchor="middle">
                {tick}
              </text>
            ))}

            {hover && <circle cx={hover.x} cy={hover.y} r={radius + 2} fill="none" stroke="var(--ivory)" strokeWidth={2} />}
            <rect x={0} y={0} width={width} height={height} fill="transparent" onPointerMove={handleMove} onPointerLeave={() => setHover(null)} />
          </svg>
        )}
        {hover && (
          <ChartTip x={hover.x} y={hover.y} chartWidth={width} value={`${hover.age}, ${hover.name}`}>
            {hover.film} ({hover.year})
          </ChartTip>
        )}
      </div>
      <p className="chart-note">Age is film year minus birth year, so it can be off by one. Each dot is one win.</p>
    </figure>
  );
}

function buildAgeSlips({ ages, eraGaps }: GoldData): StorySlip[] {
  const { actor, actress } = ages;
  const gaps = eraGaps.filter((row) => row.gap !== null).map((row) => `${row.gap} in ${row.era}`);
  const oldest = (group: AgeGroup) => group.winners[group.winners.length - 1];
  const youngest = (group: AgeGroup) => group.winners[0];

  return [
    {
      id: "gap",
      heading: "Best Actress winners run younger",
      body: `Best Actor winners average ${actor.mean} and Best Actress winners ${actress.mean}. The medians are further apart: ${actor.median} and ${actress.median}.`,
    },
    {
      id: "extremes",
      heading: "Both ends of the range",
      body: `The youngest Best Actor was ${youngest(actor).name} at ${youngest(actor).age}, and the youngest Best Actress was ${youngest(actress).name} at ${youngest(actress).age}. The oldest were ${oldest(actor).name} at ${oldest(actor).age} and ${oldest(actress).name} at ${oldest(actress).age}.`,
    },
    {
      id: "not-closing",
      heading: "The gap isn’t steadily closing",
      body: `In years by era, it runs ${gaps.join(", ")}. It has shrunk before, then widened again.`,
    },
  ];
}

function CraftLedger({ data }: { data: GoldData }) {
  const { directingWomen } = data;
  const names = joinNames(directingWomen.winners.map((winner) => winner.name));

  return (
    <motion.div className="ledger" {...rise}>
      <div className="ledger-intro">
        <h3>Women’s share of nominations</h3>
        <p>
          {directingWomen.first && (
            <>
              No woman was nominated for Best Director until {directingWomen.first.name} at the {ordinal(directingWomen.first.ceremony)}{" "}
              ceremony.{" "}
            </>
          )}
          Women have {directingWomen.nominations} Directing nominations in all, and {directingWomen.winners.length} wins:{" "}
          {names}.
        </p>
      </div>
      <div className="ledger-scroll">
        {/* Explicit roles keep this a table for screen readers when phones lay rows out as grids. */}
        <table role="table">
          <thead role="rowgroup">
            <tr role="row">
              <th role="columnheader" scope="col" aria-label="Craft" />
              {data.eras.map((era) => (
                <th key={era} role="columnheader" scope="col">
                  {era}
                </th>
              ))}
            </tr>
          </thead>
          <tbody role="rowgroup">
            {data.crafts.map((craft) => (
              <tr key={craft.craft} role="row">
                <th role="rowheader" scope="row">
                  {craft.craft}
                </th>
                {craft.eras.map((era) => (
                  <td key={era.era} role="cell">
                    {era.share === null ? "None" : formatPercent(era.share)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="ledger-note">
        Counts individual nominee credits where Wikidata records a gender. Non-binary nominees and people without gender data
        are left out of this two-way split, not counted as either.
      </p>
    </motion.div>
  );
}

function LanguageCard({ data }: { data: GoldData }) {
  const { language } = data;
  const recent = language.byEra[language.byEra.length - 1];

  return (
    <div className="language">
      <motion.div className="language-text" {...rise}>
        <h3>
          {language.nonEnglish} of {language.nominees} weren’t in English
        </h3>
        <p>
          That’s every Best Picture nominee ever, and {recent.nonEnglish} of those {language.nonEnglish} came in {recent.era}. Two have
          won: The Artist, a largely silent French film, and Parasite, the first winner in a language other than English.
        </p>
      </motion.div>
      <ul className="language-posters">
        {language.winners.map(
          (film, index) =>
            film.poster && (
              <motion.li key={film.id} {...riseAfter(index + 1)}>
                <Link to={filmHref(film.id)}>
                  <Poster path={film.poster} alt={`Poster for ${film.title}`} sizes="(max-width: 900px) 50vw, 25vw" />
                </Link>
              </motion.li>
            ),
        )}
      </ul>
    </div>
  );
}

export function WhoGetsTheGold() {
  return (
    <Act<GoldData>
      id="the-gold"
      title="Act VI: Who Gets the Gold"
      note="The envelope has favorites. They show up in who wins young, who gets nominated at all, and which languages make it onto the ballot."
      field="ivory"
      dataName="gold"
      facts={({ ages, directingWomen, language }) => [
        [`${ages.actor.mean} vs ${ages.actress.mean}`, "average age of Best Actor and Best Actress winners"],
        [String(directingWomen.winners.length), "women have won Best Director"],
        [String(language.winners.length), "Best Picture winners not in English"],
      ]}
    >
      {(data) => (
        <>
          <ScrollStory slips={buildAgeSlips(data)} renderStage={() => <AgeChart data={data} />} />
          <div className="act-table">
            <DataTableToggle
              summary="Read this chart as a table"
              headers={["Award", "Winner", "Age", "Film", "Year"]}
              rows={[
                ...data.ages.actor.winners.map((winner) => ["Best Actor", winner.name, winner.age, winner.film, winner.year]),
                ...data.ages.actress.winners.map((winner) => ["Best Actress", winner.name, winner.age, winner.film, winner.year]),
              ]}
            />
          </div>
          <CraftLedger data={data} />
          <LanguageCard data={data} />
        </>
      )}
    </Act>
  );
}
