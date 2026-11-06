import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ChartTip } from "../../charts/ChartTip";
import { DataTableToggle } from "../../charts/DataTableToggle";
import { EraBars } from "../../charts/EraBars";
import { ceremonyHref, filmHref } from "../../lib/archive";
import { formatPercent } from "../../lib/format";
import { Poster } from "../../components/Poster";
import type { FormulaData, FormulaFlag, FormulaWinner } from "../../lib/types";
import { Act } from "../Act";
import { ScrollStory } from "../ScrollStory";
import type { StorySlip } from "../ScrollStory";
import "./acts.css";

interface FormulaStep extends StorySlip {
  flag?: FormulaFlag;
  legend: string;
}

const yesNo = (value: boolean) => (value ? "Yes" : "No");

function PosterWall({ data, step }: { data: FormulaData; step: FormulaStep }) {
  const wallRef = useRef<HTMLDivElement>(null);
  const [tip, setTip] = useState<{ winner: FormulaWinner; x: number; y: number } | null>(null);

  function showTip(winner: FormulaWinner, tile: HTMLElement) {
    const wall = wallRef.current?.getBoundingClientRect();
    if (!wall) return;
    const box = tile.getBoundingClientRect();
    setTip({ winner, x: box.left - wall.left + box.width / 2, y: box.top - wall.top });
  }

  const flag = step.flag;

  return (
    <figure className="chart-figure wall-figure">
      <figcaption className="chart-legend">
        <span>{step.legend}</span>
      </figcaption>
      <div className="chart wall" ref={wallRef} onPointerLeave={() => setTip(null)}>
        {data.winners.map((winner) => (
          <Link
            key={winner.ceremony}
            to={filmHref(winner.id)}
            tabIndex={-1}
            aria-hidden="true"
            className={flag && !winner[flag] ? "wall-tile wall-tile-dim" : "wall-tile"}
            onPointerEnter={(event) => event.pointerType === "mouse" && showTip(winner, event.currentTarget)}
          >
            {winner.poster && <Poster path={winner.poster} alt="" sizes="(max-width: 900px) 8vw, 80px" />}
          </Link>
        ))}
        {tip && (
          <ChartTip x={tip.x} y={tip.y} chartWidth={wallRef.current?.clientWidth ?? 0} value={tip.winner.title}>
            Best Picture, films of {tip.winner.year}
          </ChartTip>
        )}
      </div>
      {flag && (
        <EraBars
          label={step.legend}
          bars={data.eras.map((era) => ({ era: era.era, share: era[flag] ?? 0 }))}
        />
      )}
    </figure>
  );
}

function buildSteps({ totals, eras, winners }: FormulaData): FormulaStep[] {
  const leading = (era: string) => formatPercent(eras.find((row) => row.era === era)?.mostNominated ?? 0);

  return [
    {
      id: "wall",
      heading: `${winners.length} winners, one wall`,
      body: `Every Best Picture winner in order, from ${winners[0].title} to ${winners[winners.length - 1].title}.`,
      legend: "Every Best Picture winner, oldest first",
    },
    {
      id: "directing",
      heading: "Directing is the surest companion",
      body: `${totals.directing} of ${winners.length} winners also took Directing. It is the closest thing the night has to a formula.`,
      flag: "directing",
      legend: "Lit: also won Directing",
    },
    {
      id: "editing",
      heading: "Editing is less loyal",
      body: `${totals.editing} of ${winners.length} also took Film Editing. That category began at the 7th ceremony, so the earliest years read low by construction.`,
      flag: "editing",
      legend: "Lit: also won Film Editing",
    },
    {
      id: "most-nominated",
      heading: "The leader no longer wins",
      body: `From 1970 to 1989, the nominee with the most nominations won Best Picture ${leading("1970-89")} of the time. Since 2010 it has won ${leading("2010-25")}. The field widened from five nominees to as many as ten at the 82nd ceremony.`,
      flag: "mostNominated",
      legend: "Lit: led that year’s Best Picture field in nominations, ties included",
    },
  ];
}

export function TheFormula() {
  return (
    <Act<FormulaData>
      id="the-formula"
      title="Act III: The Formula"
      note="Best Picture rarely wins alone. Some awards travel with it, and the most dependable rule of all has stopped working."
      field="gold"
      dataName="formula"
      facts={({ totals, winners }) => [
        [`${totals.directing} of ${winners.length}`, "winners also won Directing"],
        [`${totals.screenplay} of ${winners.length}`, "also won for a screenplay or story"],
        [`${totals.acting} of ${winners.length}`, "also won an acting award"],
        [`${totals.editing} of ${winners.length}`, "also won Film Editing"],
      ]}
    >
      {(data) => (
        <>
          <ScrollStory slips={buildSteps(data)} renderStage={(step) => <PosterWall data={data} step={step} />} />
          <div className="act-table">
            <DataTableToggle
              summary="Read this chart as a table"
              headers={["Ceremony", "Winner", "Directing", "Editing", "Screenplay", "Acting", "Led nominations"]}
              rows={data.winners.map((winner) => [
                <Link to={ceremonyHref(winner.ceremony)}>{winner.ceremony}</Link>,
                <Link to={filmHref(winner.id)}>{winner.title}</Link>,
                yesNo(winner.directing),
                yesNo(winner.editing),
                yesNo(winner.screenplay),
                yesNo(winner.acting),
                yesNo(winner.mostNominated),
              ])}
            />
          </div>
        </>
      )}
    </Act>
  );
}
