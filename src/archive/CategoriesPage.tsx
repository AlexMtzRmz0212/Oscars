import { Link } from "react-router-dom";
import { categoryHref } from "../lib/archive";
import type { CategoryIndexRow } from "../lib/archive";
import { ordinal } from "../lib/format";
import { useData } from "../lib/useStoryData";
import { ArchivePage, Loaded, PageHead } from "./parts";

const LATEST_CEREMONY = 98;

const lifespan = (row: CategoryIndexRow) =>
  row.lastCeremony === LATEST_CEREMONY
    ? `Since the ${ordinal(row.firstCeremony)}`
    : row.firstCeremony === row.lastCeremony
      ? `The ${ordinal(row.firstCeremony)} only`
      : `The ${ordinal(row.firstCeremony)} to the ${ordinal(row.lastCeremony)}`;

function Families({ rows }: { rows: CategoryIndexRow[] }) {
  const families = new Map<string, CategoryIndexRow[]>();
  for (const row of rows) families.set(row.family, [...(families.get(row.family) ?? []), row]);

  return (
    <div className="family-grid">
      {[...families.entries()].map(([family, members]) => (
        <section className="family" key={family} aria-label={family}>
          <h3>{family}</h3>
          <ul>
            {members.map((row) => (
              <li key={row.slug}>
                <Link to={categoryHref(row.slug)}>{row.name}</Link>
                <span>{lifespan(row)}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

export default function CategoriesPage() {
  const state = useData<CategoryIndexRow[]>("categories/index");

  return (
    <Loaded state={state}>
      {(rows) => {
        const competitive = rows.filter((row) => row.competitive);
        const others = rows.filter((row) => !row.competitive);
        return (
          <ArchivePage title="Every category">
            <PageHead title="Every category">
              <p>{competitive.length} competitive categories have come and gone, plus the Academy’s honors and technical awards.</p>
            </PageHead>
            <div className="sheet">
              <h2>Competitive</h2>
              <Families rows={competitive} />
            </div>
            <div className="sheet">
              <h2>Honors and technical awards</h2>
              <Families rows={others} />
            </div>
          </ArchivePage>
        );
      }}
    </Loaded>
  );
}
