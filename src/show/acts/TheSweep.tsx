import { useMemo, useState } from "react";
import { DataTableToggle } from "../../charts/DataTableToggle";
import { formatCount, formatShare } from "../../lib/format";
import type { SweepCell, SweepData } from "../../lib/types";
import { Act } from "../Act";
import { ScrollStory } from "../ScrollStory";
import { SeatEnvelope } from "./SeatEnvelope";
import { SeatingPlan } from "./SeatingPlan";
import { buildSteps } from "./sweepSteps";

function Story({ data }: { data: SweepData }) {
  const steps = useMemo(() => buildSteps(data), [data]);
  const [openCell, setOpenCell] = useState<SweepCell | null>(null);

  return (
    <>
      <ScrollStory slips={steps} renderStage={(step) => <SeatingPlan data={data} step={step} onOpen={setOpenCell} />} />
      <div className="act-table">
        <DataTableToggle
          summary="Read this chart as a table"
          headers={["Nominations", "Wins", "Films", "Examples"]}
          rows={data.grid.map((cell) => [
            cell.nominations,
            cell.wins,
            formatCount(cell.count),
            cell.films
              .slice(0, 3)
              .map((film) => film.title)
              .join(", "),
          ])}
        />
      </div>
      <SeatEnvelope cell={openCell} onClose={() => setOpenCell(null)} />
    </>
  );
}

export function TheSweep() {
  return (
    <Act<SweepData>
      id="the-sweep"
      title="Act II: The Sweep"
      note="The night’s headlines belong to the films that take everything. Almost nobody does. Here is every nominated film in history, seated by what it earned."
      field="velvet"
      dataName="sweep"
      facts={({ totals }) => [
        [formatCount(totals.films), "films nominated in competition"],
        [formatShare(totals.emptyHandedShare), "of them won nothing"],
        [String(totals.maxNominations), "most nominations, by Sinners"],
        [String(totals.maxWins), "most wins, shared by three films"],
      ]}
    >
      {(data) => <Story data={data} />}
    </Act>
  );
}
