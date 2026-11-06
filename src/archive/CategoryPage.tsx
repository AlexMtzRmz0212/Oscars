import { Link, useParams } from "react-router-dom";
import { ceremonyHref, nomineeHref } from "../lib/archive";
import type { CategoryPageData } from "../lib/archive";
import { ordinal, plural } from "../lib/format";
import { useData } from "../lib/useStoryData";
import { ArchivePage, EntryCredit, Loaded, PageHead } from "./parts";

const LATEST_CEREMONY = 98;

export default function CategoryPage() {
  const { slug = "" } = useParams();
  const state = useData<CategoryPageData>(`categories/${slug}`);

  return (
    <Loaded state={state} missing="There’s no category at that address.">
      {(page) => (
        <ArchivePage title={page.name}>
          <PageHead title={page.name}>
            <p>
              {page.lastCeremony === LATEST_CEREMONY ? `Awarded since the ${ordinal(page.firstCeremony)} ceremony` : `Awarded from the ${ordinal(page.firstCeremony)} ceremony to the ${ordinal(page.lastCeremony)}`},
              on {plural(page.ceremonyCount, "night")}.
            </p>
          </PageHead>

          {page.leaders.length > 1 && (
            <div className="sheet">
              <h2>Most honored here</h2>
              <ul className="leaders">
                {page.leaders.map((leader) => (
                  <li key={leader.id}>
                    <Link to={nomineeHref(leader)}>{leader.name}</Link>
                    <span className="leaders-score">
                      {plural(leader.wins, "win")} from {plural(leader.nominations, "nomination")}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="sheet">
            <h2>{page.competitive ? "Winners by night" : "Recipients by night"}</h2>
            {page.nights.map((night) => (
              <div className="night" key={night.ceremony}>
                <p className="night-when">
                  <Link to={ceremonyHref(night.ceremony)} aria-label={`${ordinal(night.ceremony)} ceremony, films of ${night.year}`}>
                    {night.year}
                  </Link>
                </p>
                <div>
                  {night.winners.map((entry, index) => (
                    <EntryCredit key={index} entry={entry} />
                  ))}
                  {night.winners.length === 0 && <p className="entry-note">No winner recorded.</p>}
                </div>
              </div>
            ))}
          </div>
        </ArchivePage>
      )}
    </Loaded>
  );
}
