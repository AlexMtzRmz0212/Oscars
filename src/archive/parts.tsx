import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Footer } from "../components/Footer";
import { SiteBar } from "../components/SiteBar";
import { categoryHref, ceremonyHref, filmHref, nomineeHref } from "../lib/archive";
import type { Entry } from "../lib/archive";
import { ordinal } from "../lib/format";
import type { DataState } from "../lib/useStoryData";
import { usePageTitle } from "../lib/usePageTitle";
import "./archive.css";

/** Matches .lead-panel and .lead-poster in archive.css. */
export const LEAD_POSTER_SIZES = "(max-width: 720px) 200px, 280px";

export function ArchivePage({ title, children }: { title?: string; children: ReactNode }) {
  usePageTitle(title);
  return (
    <>
      <div className="archive-bar">
        <SiteBar />
      </div>
      <main id="main" className="archive-main">
        {children}
      </main>
      <Footer />
    </>
  );
}

export function PageHead({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="page-head">
      <h1>{title}</h1>
      {children && <div className="page-lead">{children}</div>}
    </div>
  );
}

/** Handles the loading and missing states every Archive page shares. */
export function Loaded<T>({ state, missing, children }: { state: DataState<T>; missing?: string; children: (data: T) => ReactNode }) {
  if (state.status === "loading") {
    return (
      <>
        <div className="archive-bar">
          <SiteBar />
        </div>
        <main id="main" className="page-loading">
          <p className="archive-status" role="status">
            Opening the file…
          </p>
        </main>
      </>
    );
  }
  if (state.status === "error") {
    return (
      <ArchivePage title="Wrong envelope">
        <PageHead title="Wrong envelope">
          <p>{missing ?? "This page isn’t on the programme."}</p>
          <p>
            <Link to="/ceremonies">Browse every ceremony</Link> or <Link to="/">return to the show</Link>.
          </p>
        </PageHead>
      </ArchivePage>
    );
  }
  return <>{children(state.data)}</>;
}

export function Stats({ items }: { items: [ReactNode, string][] }) {
  return (
    <dl className="stats">
      {items.map(([value, label]) => (
        <div key={label}>
          <dt>{value}</dt>
          <dd>{label}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Won, nominated or unofficial, in words so the status never rests on colour. */
export function EntryStatus({ entry }: { entry: Entry }) {
  if (entry.unofficial) return <span className="entry-status entry-status-off">Not official</span>;
  if (entry.winner) {
    return (
      <span className="entry-status entry-status-won">
        <i aria-hidden="true" />
        {entry.competitive ? "Won" : "Honored"}
      </span>
    );
  }
  return <span className="entry-status">Nominated</span>;
}

function People({ entry, skipId }: { entry: Entry; skipId?: string }) {
  const people = entry.nominees.filter((nominee) => nominee.id !== skipId);
  if (!people.length) return null;
  return (
    <>
      {people.map((nominee, index) => (
        <span key={nominee.id}>
          {index > 0 && (index === people.length - 1 ? " and " : ", ")}
          <Link to={nomineeHref(nominee)}>{nominee.name}</Link>
        </span>
      ))}
    </>
  );
}

function Films({ entry, skipId }: { entry: Entry; skipId?: string }) {
  const films = entry.films.filter((film) => film.id !== skipId);
  if (!films.length) return null;
  return (
    <>
      {films.map((film, index) => (
        <span key={film.id}>
          {index > 0 && (index === films.length - 1 ? " and " : ", ")}
          <Link className="entry-film" to={filmHref(film.id)}>
            {film.title}
          </Link>
        </span>
      ))}
    </>
  );
}

const LONG_NOTE = 90;

function EntryNote({ note }: { note: string }) {
  if (note.length <= LONG_NOTE) return <p className="entry-note">{note}</p>;
  return (
    <details className="entry-note">
      <summary>Note from the record</summary>
      {note}
    </details>
  );
}

/** What was nominated, leaving out whichever film or person the page is already about. */
export function EntryCredit({ entry, skipId }: { entry: Entry; skipId?: string }) {
  const films = entry.films.filter((film) => film.id !== skipId);
  const people = entry.nominees.filter((nominee) => nominee.id !== skipId);
  const empty = !films.length && !people.length;

  return (
    <div className="entry-credit">
      <p>
        {empty && (entry.citation ?? "On the record without a named recipient.")}
        <Films entry={entry} skipId={skipId} />
        {films.length > 0 && people.length > 0 && <span className="entry-sep">, </span>}
        <People entry={entry} skipId={skipId} />
      </p>
      {entry.detail && <p className="entry-detail">{entry.detail}</p>}
      {entry.note && <EntryNote note={entry.note} />}
      {!empty && !entry.competitive && entry.citation && <p className="entry-note">{entry.citation}</p>}
    </div>
  );
}

export function EntryRow({ entry, skipId, lead }: { entry: Entry; skipId?: string; lead?: ReactNode }) {
  return (
    <li className={entry.winner ? "entry entry-winner" : "entry"}>
      <EntryStatus entry={entry} />
      <div className="entry-body">
        {lead}
        <EntryCredit entry={entry} skipId={skipId} />
      </div>
    </li>
  );
}

/** A person's or film's record, newest first, grouped under each ceremony. */
export function FullRecord({ entries, skipId }: { entries: Entry[]; skipId: string }) {
  const nights = new Map<number, Entry[]>();
  for (const entry of entries) nights.set(entry.ceremony, [...(nights.get(entry.ceremony) ?? []), entry]);
  const ordered = [...nights.entries()].sort(([a], [b]) => b - a);

  return (
    <div className="sheet">
      <h2>The record</h2>
      <div className="sheet-columns">
        {ordered.map(([ceremony, rows]) => (
          <section className="record-night" key={ceremony} aria-label={`${ordinal(ceremony)} ceremony`}>
            <h3>
              <Link to={ceremonyHref(ceremony)}>
                {ordinal(ceremony)} ceremony, films of {rows[0].year}
              </Link>
            </h3>
            <ul className="entries">
              {rows.map((entry, index) => (
                <EntryRow
                  key={index}
                  entry={entry}
                  skipId={skipId}
                  lead={
                    <p className="entry-category">
                      <Link to={categoryHref(entry.slug)}>{entry.category}</Link>
                    </p>
                  }
                />
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}

