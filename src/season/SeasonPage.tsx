import { useMemo } from "react";
import { Link } from "react-router-dom";
import { ArchivePage, Loaded, PageHead } from "../archive/parts";
import { DataTableToggle } from "../charts/DataTableToggle";
import { linearScale } from "../charts/scales";
import { useChartSize } from "../charts/useChartSize";
import { Poster } from "../components/Poster";
import { formatPercent, plural } from "../lib/format";
import { useData } from "../lib/useStoryData";
import type { BacktestData, BacktestTally, SeasonContest, SeasonData } from "./types";
import "./season.css";

const DAY_MS = 86_400_000;
/** Picks this close count as a tie, because one night either way moves the rate about this much. */
const TIE_MARGIN = 0.02;

const dateFormat = new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", year: "numeric", timeZone: "UTC" });
const longDate = (date: string) => dateFormat.format(new Date(`${date}T00:00:00Z`));

function daysUntil(date: string, now: number) {
  return Math.ceil((new Date(`${date}T00:00:00Z`).getTime() - now) / DAY_MS);
}

function Schedule({ schedule }: { schedule: SeasonData["schedule"] }) {
  const now = useMemo(() => Date.now(), []);
  const next = schedule.find((item) => daysUntil(item.date, now) > 0);

  return (
    <div className="season-schedule">
      {next && (
        <p className="season-next">
          <strong>{daysUntil(next.date, now)}</strong>
          <span>{daysUntil(next.date, now) === 1 ? "day" : "days"} until: {next.label.toLowerCase()}</span>
        </p>
      )}
      <ol>
        {schedule.map((item) => (
          <li key={item.label} className={daysUntil(item.date, now) <= 0 ? "season-past" : undefined}>
            <span className="season-date">{longDate(item.date)}</span>
            <span>{item.label}</span>
          </li>
        ))}
      </ol>
      <p className="season-small">The Academy says its dates may change.</p>
    </div>
  );
}

function ContestCard({ contest, frozen }: { contest: SeasonContest; frozen: boolean }) {
  return (
    <section className="contest" aria-label={contest.label}>
      <h3>{contest.label}</h3>
      {!frozen && (
        <p className="season-small">
          {contest.awardsAnnounced} of {contest.awardsTotal} precursor awards announced
        </p>
      )}
      {contest.correct != null && <p className="contest-verdict">{contest.correct ? "The forecast got this right." : "The forecast got this wrong."}</p>}
      <ol className="contest-nominees">
        {contest.nominees.map((nominee) => (
          <li key={nominee.label} className={nominee.won ? "contest-winner" : undefined}>
            {nominee.poster ? <Poster path={nominee.poster} alt="" sizes="44px" /> : <span className="contest-no-poster" />}
            <div className="contest-body">
              <div className="contest-line">
                <span className="contest-name">
                  {nominee.link ? <Link to={nominee.link}>{nominee.label}</Link> : nominee.label}
                  {nominee.won && <span className="contest-won"> Won the Oscar</span>}
                </span>
                <span className="contest-odds">{formatPercent(nominee.probability)}</span>
              </div>
              <span className="contest-track" aria-hidden="true">
                <span className={nominee.won ? "contest-fill contest-fill-won" : "contest-fill"} style={{ width: `${nominee.probability * 100}%` }} />
              </span>
              {nominee.precursors.length > 0 && <p className="season-small">Precursors: {nominee.precursors.join(", ")}</p>}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Board({ season }: { season: SeasonData }) {
  if (season.stage === "awaiting-nominations") {
    const nominations = season.schedule.find((item) => item.label.startsWith("Nominations"));
    return (
      <div className="sheet season-empty">
        <h2>No forecast yet</h2>
        <p>The forecast opens once the nominees are announced{nominations ? ` on ${longDate(nominations.date)}` : ""}, and updates as each precursor award lands. Until then, here is how it would have done in the past.</p>
      </div>
    );
  }

  const frozen = season.stage === "frozen" || season.stage === "scored";
  const frozenOn = season.frozenAt ? longDate(season.frozenAt.slice(0, 10)) : "";
  return (
    <div className="sheet">
      <h2>{season.stage === "scored" ? "How the forecast did" : "The forecast"}</h2>
      <p className="season-board-note">
        {season.stage === "open" && "Live odds, changing as precursor awards are announced."}
        {season.stage === "frozen" && `Frozen on ${frozenOn}, before the envelopes opened.`}
        {season.stage === "scored" && season.score && `Frozen on ${frozenOn}. Its top pick was right in ${season.score.hits} of ${plural(season.score.nights, "category", "categories")} so far.`}
      </p>
      <div className="contest-grid">
        {season.contests.map((contest) => (
          <ContestCard key={contest.key} contest={contest} frozen={frozen} />
        ))}
      </div>
    </div>
  );
}

/** Says plainly how the picks compare, whichever way the numbers fall. */
function comparison(model: BacktestTally, rule: BacktestTally) {
  const gap = (model.hitRate ?? 0) - (rule.hitRate ?? 0);
  if (Math.abs(gap) <= TIE_MARGIN) return "about the same as";
  return gap > 0 ? "better than" : "worse than";
}

function Calibration({ rows }: { rows: BacktestData["calibration"] }) {
  const { ref, width, height } = useChartSize({ ratio: 1, pinnedShare: 0.5, reserved: 200 });
  const side = Math.min(width, height, 460);
  const margin = 44;
  const scale = linearScale([0, 1], [margin, side - 10]);
  const flip = linearScale([0, 1], [side - margin + 8, 10]);
  const ticks = [0, 0.25, 0.5, 0.75, 1];

  return (
    <figure className="calibration chart-figure">
      <div className="chart" ref={ref}>
        {side > 0 && (
          <svg width={side} height={side} role="img" aria-label="Predicted chance against how often those nominees actually won. Points near the diagonal mean the odds were honest.">
            {ticks.map((tick) => (
              <g key={tick}>
                <line className="chart-grid" x1={margin} x2={side - 10} y1={flip(tick)} y2={flip(tick)} />
                <text className="chart-text" x={margin - 6} y={flip(tick) + 4} textAnchor="end">
                  {formatPercent(tick)}
                </text>
                <text className="chart-text" x={scale(tick)} y={side - margin + 26} textAnchor="middle">
                  {formatPercent(tick)}
                </text>
              </g>
            ))}
            <line x1={scale(0)} y1={flip(0)} x2={scale(1)} y2={flip(1)} stroke="var(--data-nominated)" strokeWidth={2} />
            {rows.map((row) => (
              <circle key={row.from} cx={scale(row.predicted)} cy={flip(row.actual)} r={7} fill="var(--ivory)" stroke="var(--velvet-black)" strokeWidth={2}>
                <title>
                  Said {formatPercent(row.predicted)}, happened {formatPercent(row.actual)}, across {plural(row.nominees, "nominee")}
                </title>
              </circle>
            ))}
          </svg>
        )}
      </div>
      <figcaption className="season-small">Across: what the model said. Up: how often it happened. On the line means honest odds.</figcaption>
    </figure>
  );
}

/** The most confident miss, because a record that hides its worst night isn’t much of a record. */
function worstMiss(contests: BacktestData["contests"]) {
  const misses = contests.flatMap((contest) => contest.nights.filter((night) => !night.correct));
  return misses.reduce<(typeof misses)[number] | null>((worst, night) => (!worst || night.pickProbability > worst.pickProbability ? night : worst), null);
}

function TrackRecord({ backtest }: { backtest: BacktestData }) {
  const { overall, contests } = backtest;
  const rule = overall.precursorCount;
  const model = overall.model;
  const tiedWithRule = comparison(model, rule) === "about the same as";
  const miss = worstMiss(contests);

  return (
    <>
      <h2 className="section-title">Would it have worked?</h2>
      <div className="season-record">
        <div className="season-record-text">
          <p className="season-big">{formatPercent(model.hitRate ?? 0)}</p>
          <p className="season-lead">
            of its {model.nights} top picks were right, from {backtest.firstYear} to {backtest.lastYear}. Each year was predicted using only earlier years, so it never saw the future.
          </p>
          <p>
            That is {comparison(model, overall.mostNominated)} backing the most-nominated film ({formatPercent(overall.mostNominated.hitRate ?? 0)}), and {comparison(model, rule)} simply backing whoever won the most precursors ({formatPercent(rule.hitRate ?? 0)}).
          </p>
          <p>
            {tiedWithRule && "So the model’s edge isn’t in its picks. "}
            Counting precursor wins gets you a name but no sense of how sure to be, or who is close behind. The model gives odds, and the chart shows how close those odds have come to what happened.
          </p>
          {miss && (
            <p className="season-small">
              Its most confident miss: {formatPercent(miss.pickProbability)} on {miss.pick} in {miss.year}, the year {miss.winner} won.
            </p>
          )}
        </div>
        <Calibration rows={backtest.calibration} />
      </div>

      <div className="sheet">
        <h2>By category</h2>
        <div className="season-table-scroll">
          <table className="season-table">
            <thead>
              <tr>
                <th scope="col">Category</th>
                <th scope="col">Model</th>
                <th scope="col">Most precursors</th>
                <th scope="col">Most nominated</th>
                <th scope="col">Chance</th>
              </tr>
            </thead>
            <tbody>
              {contests.map((contest) => (
                <tr key={contest.key}>
                  <th scope="row">{contest.label}</th>
                  <td>{formatPercent(contest.model.hitRate ?? 0)}</td>
                  <td>{formatPercent(contest.precursorCount.hitRate ?? 0)}</td>
                  <td>{formatPercent(contest.mostNominated.hitRate ?? 0)}</td>
                  <td>{formatPercent(contest.chance.hitRate ?? 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="season-small">
          Share of {contests[0]?.model.nights ?? 0} years each rule picked the winner, with a tie at the top earning part of a hit. That is one number per category over about two decades, so small gaps mean little.
        </p>
      </div>

      <div className="sheet">
        <h2>Every pick</h2>
        {contests.map((contest, index) => (
          <details key={contest.key} className="season-picks" open={index === 0}>
            <summary>
              {contest.label}: {contest.nights.filter((night) => night.correct).length} of {contest.nights.length} right
            </summary>
            <p className="season-small">What it weighs most: {contest.weights.filter((weight) => weight.weight > 0).slice(0, 4).map((weight) => weight.label).join(", ")}.</p>
            <ul>
              {contest.nights.map((night) => (
                <li key={night.ceremony} className={night.correct ? "pick-right" : "pick-wrong"}>
                  <span className="pick-year">{night.year}</span>
                  <span className="pick-status">{night.correct ? "Right" : "Missed"}</span>
                  <span>
                    {night.correct ? (
                      <>
                        {night.winner}, at {formatPercent(night.winnerProbability)}
                      </>
                    ) : (
                      <>
                        Picked {night.pick} at {formatPercent(night.pickProbability)}. {night.winner} won, at {formatPercent(night.winnerProbability)}.
                      </>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </details>
        ))}
      </div>

      <div className="act-table season-calibration-table">
        <DataTableToggle
          summary="Read the honesty chart as a table"
          headers={["The model said", "It happened", "Nominees"]}
          rows={backtest.calibration.map((row) => [formatPercent(row.predicted), formatPercent(row.actual), row.nominees])}
        />
      </div>

      <div className="sheet">
        <h2>How it works</h2>
        <ul className="season-how">
          <li>It forecasts six categories: Picture, Director and the four acting awards.</li>
          <li>It reads what the ballot says about each nominee, such as a film’s total nominations or whether it’s also up for Film Editing, plus each precursor win.</li>
          <li>It learned how much each of those has mattered since {backtest.trainingStarts}. Odds in a category always add up to 100%, because a category has one winner.</li>
          <li>It never sees who won a night before predicting it, and BAFTA is ignored before films of 2000, when it was held after the Oscars.</li>
          <li>The forecast freezes the day before the ceremony. After that it can’t be changed, so the score can’t be flattered. It’s here for fun, not for betting.</li>
        </ul>
      </div>
    </>
  );
}

export default function SeasonPage() {
  const season = useData<SeasonData>("season/season");
  const backtest = useData<BacktestData>("season/backtest");

  return (
    <Loaded state={season} missing="The season’s forecast didn’t load. Refresh the page to try again.">
      {(data) => (
        <ArchivePage title="The 99th">
          <PageHead title="The 99th">
            <p>A forecast for the next envelopes, with its past record in full.</p>
            <Schedule schedule={data.schedule} />
          </PageHead>
          <Board season={data} />
          {backtest.status === "ready" && <TrackRecord backtest={backtest.data} />}
          {backtest.status === "error" && (
            <p className="archive-status" role="alert">
              The track record didn’t load. Refresh the page to try again.
            </p>
          )}
        </ArchivePage>
      )}
    </Loaded>
  );
}
