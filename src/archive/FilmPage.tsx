import { Link, useParams } from "react-router-dom";
import { ceremonyHref, shardOf } from "../lib/archive";
import type { FilmPageData } from "../lib/archive";
import { formatCount, formatDollars, ordinal, plural } from "../lib/format";
import { Poster } from "../components/Poster";
import { useData } from "../lib/useStoryData";
import { ArchivePage, FullRecord, LEAD_POSTER_SIZES, Loaded, Stats } from "./parts";

const languageNames = new Intl.DisplayNames(["en"], { type: "language" });
const regionNames = new Intl.DisplayNames(["en"], { type: "region" });

function displayName(names: Intl.DisplayNames, code: string) {
  try {
    return names.of(code) ?? code;
  } catch {
    return code;
  }
}

function rankSentence({ rank }: FilmPageData) {
  if (!rank) return null;
  const night = <Link to={ceremonyHref(rank.ceremony)}>the {ordinal(rank.ceremony)} ceremony</Link>;
  return rank.rank === 1 ? (
    <>The most-nominated film at {night}, ties included.</>
  ) : (
    <>
      Ranked {ordinal(rank.rank)} by nominations among {formatCount(rank.of)} films at {night}.
    </>
  );
}

function Facts({ film }: { film: FilmPageData }) {
  const facts: [string, string][] = [];
  if (film.rating) facts.push(["TMDB audience score", `${film.rating.toFixed(1)} from ${plural(film.votes ?? 0, "vote")}`]);
  if (film.revenue) facts.push(["Worldwide gross, TMDB", formatDollars(film.revenue)]);
  if (film.budget) facts.push(["Budget, TMDB", formatDollars(film.budget)]);
  if (film.runtime) facts.push(["Runtime", `${film.runtime} minutes`]);
  if (film.language) facts.push(["Original language", displayName(languageNames, film.language)]);
  if (film.countries.length) facts.push(["Made in", film.countries.map((code) => displayName(regionNames, code)).join(", ")]);
  if (film.genres.length) facts.push(["Genres", film.genres.join(", ")]);
  if (!facts.length) return null;

  return (
    <dl className="fact-list">
      {facts.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function FilmPage() {
  const { id = "" } = useParams();
  const state = useData<Record<string, FilmPageData>>(`films/${shardOf(id)}`);

  return (
    <Loaded state={state} missing="No film in the record has that id.">
      {(shard) => {
        const film = shard[id];
        if (!film) return <Loaded state={{ status: "error" }} missing="No film in the record has that id.">{() => null}</Loaded>;
        const stats: [string, string][] = [
          [String(film.nominations), film.nominations === 1 ? "nomination" : "nominations"],
          [String(film.wins), film.wins === 1 ? "win" : "wins"],
        ];
        if (film.honors) stats.push([String(film.honors), film.honors === 1 ? "honor" : "honors"]);
        return (
          <ArchivePage title={film.title}>
            <div className="lead-panel">
              {film.poster && <Poster className="lead-poster" path={film.poster} alt={`Poster for ${film.title}`} sizes={LEAD_POSTER_SIZES} priority />}
              <div className="lead-text">
                <h1>{film.title}</h1>
                <p className="lead-sub">Awards year {film.year}</p>
                <Stats items={stats} />
                {film.rank && <p>{rankSentence(film)}</p>}
                <Facts film={film} />
              </div>
            </div>
            <FullRecord entries={film.entries} skipId={film.id} />
          </ArchivePage>
        );
      }}
    </Loaded>
  );
}
