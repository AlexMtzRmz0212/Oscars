import { Link, useParams } from "react-router-dom";
import { findYearEntry, YearCard, yearRange } from "../components/YearCard";
import { bornHref } from "../lib/archive";
import type { EncoreEntry } from "../lib/types";
import { useStoryData } from "../lib/useStoryData";
import { ArchivePage, Loaded, PageHead } from "./parts";

export default function BornPage() {
  const { year: yearText = "" } = useParams();
  const state = useStoryData<EncoreEntry[]>("encore");
  const year = Number(yearText);

  return (
    <Loaded state={state}>
      {(entries) => {
        const { first, last } = yearRange(entries);
        const entry = Number.isInteger(year) ? findYearEntry(entries, year) : undefined;

        if (!entry) {
          return (
            <ArchivePage title="Wrong envelope">
              <PageHead title="Wrong envelope">
                <p>
                  The record runs from {first} to {last}. Try the <Link to={bornHref(1997)}>envelope for 1997</Link>.
                </p>
              </PageHead>
            </ArchivePage>
          );
        }

        return (
          <ArchivePage title={`What won in ${year}`}>
            <PageHead title={`What won in ${year}`}>
              <p>The biggest envelopes for films of that year.</p>
              <div className="born-card">
                <YearCard entry={entry} headingLevel={2} />
              </div>
            </PageHead>
            <nav className="pager" aria-label="Other years">
              {year > first ? <Link to={bornHref(year - 1)}>Previous: {year - 1}</Link> : <span />}
              {year < last && <Link to={bornHref(year + 1)}>Next: {year + 1}</Link>}
            </nav>
          </ArchivePage>
        );
      }}
    </Loaded>
  );
}
