import MiniSearch from "minisearch";
import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { plural } from "../lib/format";
import { useData } from "../lib/useStoryData";
import "./SearchDialog.css";

type Kind = "film" | "person" | "studio" | "category" | "ceremony";

interface SearchRow {
  k: Kind;
  i: string;
  n: string;
  y?: number;
  w: number;
  c: number;
}

const MAX_RESULTS = 12;
const KIND_LABELS: Record<Kind, string> = { film: "Film", person: "Person", studio: "Studio", category: "Category", ceremony: "Ceremony" };
const KIND_PATHS: Record<Kind, string> = { film: "/films/", person: "/people/", studio: "/studios/", category: "/categories/", ceremony: "/ceremonies/" };

const hrefOf = (row: SearchRow) => `${KIND_PATHS[row.k]}${row.i}`;
const keyOf = (row: SearchRow) => `${row.k}:${row.i}`;

function describe(row: SearchRow) {
  const parts: (string | number)[] = [KIND_LABELS[row.k]];
  if (row.y) parts.push(row.y);
  if (row.c) parts.push(plural(row.c, "nomination"));
  if (row.w) parts.push(plural(row.w, "win"));
  return parts.join(", ");
}

/** Names can be searched without accents, and a query may be a year. */
const normalizeTerm = (term: string) => term.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

function buildIndex(rows: SearchRow[]) {
  const index = new MiniSearch<SearchRow & { id: string; year: string }>({
    fields: ["n", "year"],
    storeFields: [],
    processTerm: normalizeTerm,
    searchOptions: {
      prefix: true,
      fuzzy: (term) => (term.length > 3 ? 0.2 : 0),
      combineWith: "AND",
      boost: { n: 3 },
      // A well-known film should beat an obscure namesake.
      boostDocument: (id) => 1 + Math.log1p(byKey.get(String(id))?.c ?? 0) / 2,
    },
  });
  const byKey = new Map(rows.map((row) => [keyOf(row), row]));
  index.addAll(rows.map((row) => ({ ...row, id: keyOf(row), year: row.y ? String(row.y) : "" })));
  return { index, byKey };
}

export default function SearchDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const data = useData<SearchRow[]>("search");
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      inputRef.current?.select();
    }
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const engine = useMemo(() => (data.status === "ready" ? buildIndex(data.data) : null), [data]);

  const results = useMemo(() => {
    const text = query.trim();
    if (!engine || text.length < 2) return [];
    return engine.index
      .search(text)
      .slice(0, MAX_RESULTS)
      .map((match) => engine.byKey.get(String(match.id)))
      .filter((row): row is SearchRow => Boolean(row));
  }, [engine, query]);

  useEffect(() => setActive(0), [results]);

  function go(row: SearchRow) {
    onClose();
    navigate(hrefOf(row));
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      // A search field would otherwise spend the first Escape on clearing itself.
      event.preventDefault();
      onClose();
    } else if (event.key === "ArrowDown" && results.length) {
      event.preventDefault();
      setActive((current) => (current + 1) % results.length);
    } else if (event.key === "ArrowUp" && results.length) {
      event.preventDefault();
      setActive((current) => (current - 1 + results.length) % results.length);
    } else if (event.key === "Enter" && results[active]) {
      event.preventDefault();
      go(results[active]);
    }
  }

  const trimmed = query.trim();
  const empty = engine && trimmed.length >= 2 && results.length === 0;

  return (
    <dialog
      ref={dialogRef}
      className="search-dialog"
      aria-label="Search the Archive"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
    >
      <div className="search-sheet">
        <div className="search-head">
          <label htmlFor="search-input">Search every film, person, studio, category and ceremony</label>
          <button type="button" className="button" onClick={onClose}>
            Close
          </button>
        </div>
        <input
          id="search-input"
          name="search"
          ref={inputRef}
          type="search"
          role="combobox"
          aria-expanded={results.length > 0}
          aria-controls="search-results"
          aria-activedescendant={results[active] ? `search-option-${active}` : undefined}
          autoComplete="off"
          placeholder="Parasite, Meryl Streep, 1997…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={handleKeyDown}
        />

        {data.status === "loading" && <p className="search-status">Opening the card catalog…</p>}
        {data.status === "error" && (
          <p className="search-status" role="alert">
            Search didn’t load. Refresh the page to try again.
          </p>
        )}
        {empty && <p className="search-status">Nothing matches “{trimmed}”. Try fewer letters.</p>}

        <ul id="search-results" role="listbox" aria-label="Results" className="search-results">
          {results.map((row, index) => (
            <li
              key={keyOf(row)}
              id={`search-option-${index}`}
              role="option"
              aria-selected={index === active}
              className={index === active ? "search-result search-result-active" : "search-result"}
              onPointerEnter={() => setActive(index)}
            >
              <Link to={hrefOf(row)} tabIndex={-1} onClick={onClose}>
                <span className="search-name">{row.n}</span>
                <span className="search-meta">{describe(row)}</span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </dialog>
  );
}
