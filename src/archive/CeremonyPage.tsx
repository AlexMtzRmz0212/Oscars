import { Link, useParams } from "react-router-dom";
import { categoryHref, ceremonyHref, filmHref } from "../lib/archive";
import type { CeremonyPageData } from "../lib/archive";
import { ordinal, plural } from "../lib/format";
import { Poster } from "../components/Poster";
import { useData } from "../lib/useStoryData";
import { ArchivePage, EntryRow, LEAD_POSTER_SIZES, Loaded } from "./parts";

const LATEST = 98;

function Ballot({ title, categories }: { title: string; categories: CeremonyPageData["categories"] }) {
  if (!categories.length) return null;
  return (
    <div className="sheet">
      <h2>{title}</h2>
      <div className="sheet-columns">
        {categories.map((category) => (
          <section className="ballot-category" key={category.slug} aria-label={category.name}>
            <h3>
              <Link to={categoryHref(category.slug)}>{category.name}</Link>
            </h3>
            <ul className="entries">
              {category.entries.map((entry, index) => (
                <EntryRow key={index} entry={entry} />
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}

export default function CeremonyPage() {
  const { number } = useParams();
  const state = useData<CeremonyPageData>(`ceremonies/${number}`);

  return (
    <Loaded state={state} missing="There’s no ceremony with that number.">
      {(page) => {
        const name = `The ${ordinal(page.ceremony)} ceremony`;
        return (
          <ArchivePage title={name}>
            <div className="lead-panel">
              {page.bestPicture?.poster && <Poster className="lead-poster" path={page.bestPicture.poster} alt={`Poster for ${page.bestPicture.title}`} sizes={LEAD_POSTER_SIZES} priority />}
              <div className="lead-text">
                <h1>{name}</h1>
                <p className="lead-sub">
                  Films of {page.year}, with {plural(page.competitiveCategories, "competitive category", "competitive categories")}.
                </p>
                {page.bestPicture && (
                  <p className="lead-sub">
                    Best Picture: <Link to={filmHref(page.bestPicture.id)}>{page.bestPicture.title}</Link>
                  </p>
                )}
              </div>
            </div>
            <nav className="pager" aria-label="Other ceremonies">
              {page.ceremony > 1 ? <Link to={ceremonyHref(page.ceremony - 1)}>Previous: the {ordinal(page.ceremony - 1)}</Link> : <span />}
              {page.ceremony < LATEST && <Link to={ceremonyHref(page.ceremony + 1)}>Next: the {ordinal(page.ceremony + 1)}</Link>}
            </nav>
            <Ballot title="The ballot" categories={page.categories.filter((category) => category.competitive)} />
            <Ballot title="Honors and technical awards" categories={page.categories.filter((category) => !category.competitive)} />
          </ArchivePage>
        );
      }}
    </Loaded>
  );
}
