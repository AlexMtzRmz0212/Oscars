import { Link } from "react-router-dom";
import { filmHref } from "../lib/archive";
import { joinNames, ordinal } from "../lib/format";
import { Poster } from "./Poster";
import type { EncoreEntry } from "../lib/types";
import "./YearCard.css";

/** A split season like 1932/33 answers for both years, and the earlier ceremony wins an overlap. */
export function findYearEntry(entries: EncoreEntry[], year: number) {
  return entries.find((entry) => {
    const [start, end] = entry.year.split("/");
    const first = Number(start);
    const last = end ? Math.floor(first / 100) * 100 + Number(end) : first;
    return year >= first && year <= last;
  });
}

export function yearRange(entries: EncoreEntry[]) {
  return { first: Number(entries[0].year.split("/")[0]), last: Number(entries[entries.length - 1].year.split("/")[0]) };
}

/** A year's big winners, on a card rising out of a gold envelope. */
export function YearCard({ entry, headingLevel = 3 }: { entry: EncoreEntry; headingLevel?: 2 | 3 }) {
  const Heading = headingLevel === 2 ? "h2" : "h3";
  const rows: [string, string[]][] = [
    ["Best Director", entry.director],
    ["Best Actor", entry.actor],
    ["Best Actress", entry.actress],
  ];

  return (
    <div className="year-opened" key={entry.ceremony}>
      <div className="year-card">
        {entry.picture?.poster && (
          <Poster path={entry.picture.poster} alt={`Poster for ${entry.picture.title}`} sizes="(max-width: 560px) 150px, 200px" priority />
        )}
        <div>
          <p className="year-season">
            Films of {entry.year}, honored at the <Link to={`/ceremonies/${entry.ceremony}`}>{ordinal(entry.ceremony)} ceremony</Link>
          </p>
          <Heading>{entry.picture ? <Link to={filmHref(entry.picture.id)}>{entry.picture.title}</Link> : "No winner recorded"}</Heading>
          <p className="year-award">Best Picture</p>
          <dl>
            {rows.map(([award, names]) => (
              <div key={award}>
                <dt>{award}</dt>
                <dd>{joinNames(names)}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
      <div className="year-pocket" aria-hidden="true" />
    </div>
  );
}
