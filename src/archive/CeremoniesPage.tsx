import { Link } from "react-router-dom";
import { ceremonyHref } from "../lib/archive";
import type { CeremonyIndexRow } from "../lib/archive";
import { ordinal } from "../lib/format";
import { Poster } from "../components/Poster";
import { useData } from "../lib/useStoryData";
import { ArchivePage, Loaded, PageHead } from "./parts";

export default function CeremoniesPage() {
  const state = useData<CeremonyIndexRow[]>("ceremonies/index");

  return (
    <Loaded state={state}>
      {(rows) => (
        <ArchivePage title="Every ceremony">
          <PageHead title="Every ceremony">
            <p>{rows.length} nights, newest first. Open any one for its full ballot.</p>
          </PageHead>
          <ol className="ceremony-wall" reversed>
            {[...rows].reverse().map((row) => (
              <li className="ceremony-tile" key={row.ceremony}>
                <Link to={ceremonyHref(row.ceremony)}>
                  {row.bestPicture?.poster && <Poster path={row.bestPicture.poster} alt="" sizes="(max-width: 700px) 30vw, 12vw" />}
                  <span className="ceremony-number">{ordinal(row.ceremony)}</span>
                  <span>{row.bestPicture?.title}</span>
                  <span className="ceremony-title">Films of {row.year}</span>
                </Link>
              </li>
            ))}
          </ol>
        </ArchivePage>
      )}
    </Loaded>
  );
}
