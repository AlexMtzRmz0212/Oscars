import { DataTableToggle } from "../../charts/DataTableToggle";
import { EraBars } from "../../charts/EraBars";
import { formatPercent, ordinal } from "../../lib/format";
import type { AudienceData } from "../../lib/types";
import { Act } from "../Act";
import { ScrollStory } from "../ScrollStory";
import type { StorySlip } from "../ScrollStory";
import "./acts.css";

interface AudienceStep extends StorySlip {
  highlight: (rank: number) => boolean;
  showEras?: boolean;
}

const LOW_RANK = 5;

function RankBars({ data, step }: { data: AudienceData; step: AudienceStep }) {
  const most = Math.max(...data.ranks.map((row) => row.ceremonies));
  const chanceCount = data.chance * data.ceremoniesCompared;

  return (
    <figure className="chart-figure">
      <figcaption className="chart-legend">
        <span>Where the winner ranked among that year’s nominees, by TMDb audience score</span>
      </figcaption>
      <ul className="rank-bars" aria-label="Ceremonies by the winner’s rank in audience score">
        {data.ranks.map((row) => (
          <li key={row.rank} className={step.highlight(row.rank) ? "" : "rank-dim"}>
            <span className="rank-label">{ordinal(row.rank)}</span>
            <span className="rank-track">
              <span
                className={row.rank === 1 ? "rank-fill rank-fill-top" : "rank-fill"}
                style={{ width: `${(row.ceremonies / most) * 100}%` }}
              />
              <span className="rank-value">{row.ceremonies}</span>
              {row.rank === 1 && (
                <span className="rank-chance" style={{ left: `${(chanceCount / most) * 100}%` }}>
                  <span>Chance: {Math.round(chanceCount)}</span>
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
      {step.showEras && (
        <EraBars
          label="How often the audience’s favorite won, by era"
          bars={data.eras
            .filter((era) => era.ceremonies > 0)
            .map((era) => ({ era: era.era, share: era.favouriteWon / era.ceremonies, detail: `${era.favouriteWon} of ${era.ceremonies}` }))}
        />
      )}
    </figure>
  );
}

function buildSteps(data: AudienceData): AudienceStep[] {
  const favourite = data.ranks.find((row) => row.rank === 1)?.ceremonies ?? 0;
  const low = data.ranks.filter((row) => row.rank >= LOW_RANK).reduce((sum, row) => sum + row.ceremonies, 0);
  const left = data.ceremoniesTotal - data.ceremoniesCompared;
  const [widest, second] = data.widestGaps;

  return [
    {
      id: "favourite",
      heading: "The favorite often wins",
      body: `In ${favourite} of ${data.ceremoniesCompared} ceremonies the winner had the field’s top audience score, about ${formatPercent(favourite / data.ceremoniesCompared)}. Chance alone gives ${formatPercent(data.chance)}. Another ${left} ceremonies have a nominee with too few votes to compare.`,
      highlight: (rank) => rank === 1,
    },
    {
      id: "eras",
      heading: "It peaked in the 1970s and 80s",
      body: "The favorite’s win rate climbs to its peak in 1970-89, then falls. The fields are bigger since 2009, so a lower rate is partly arithmetic.",
      highlight: (rank) => rank === 1,
      showEras: true,
    },
    {
      id: "low",
      heading: `${low} winners ranked ${ordinal(LOW_RANK)} or lower`,
      body: `Widest gap: ${widest.winner.title} scores ${widest.winner.rating.toFixed(1)} on TMDb, and it beat ${widest.favourite.title} at ${widest.favourite.rating.toFixed(1)}. Next: ${second.winner.title} at ${second.winner.rating.toFixed(1)} over ${second.favourite.title} at ${second.favourite.rating.toFixed(1)}.`,
      highlight: (rank) => rank >= LOW_RANK,
      plates: [widest.winner, widest.favourite, second.winner],
    },
    {
      id: "caveat",
      heading: "These are today’s scores",
      body: "They come from people voting now, not in the year of release, and winning may lift a film’s score. This shows agreement, not cause.",
      highlight: () => true,
    },
  ];
}

export function TheAudience() {
  return (
    <Act<AudienceData>
      id="the-audience"
      title="Act V: The Audience Votes"
      note="TMDb’s users have scored nearly every nominee. Line their scores up against the envelope and the two agree more often than you might guess."
      field="oxblood"
      dataName="audience"
      facts={(data) => {
        const favourite = data.ranks.find((row) => row.rank === 1)?.ceremonies ?? 0;
        return [
          [`${favourite} of ${data.ceremoniesCompared}`, "winners were the audience’s top pick"],
          [formatPercent(data.chance), "what chance would give"],
        ];
      }}
    >
      {(data) => (
        <>
          <ScrollStory slips={buildSteps(data)} renderStage={(step) => <RankBars data={data} step={step} />} />
          <div className="act-table">
            <DataTableToggle
              summary="Read this chart as a table"
              headers={["Ceremony", "Films of", "Winner", "Winner’s score", "Audience favorite", "Favorite’s score", "Winner’s rank"]}
              rows={data.nights.map((night) => [
                night.ceremony,
                night.year,
                night.winner.title,
                night.winner.rating.toFixed(1),
                night.favourite.title,
                night.favourite.rating.toFixed(1),
                `${ordinal(night.rank)} of ${night.size}`,
              ])}
            />
          </div>
        </>
      )}
    </Act>
  );
}
