import { ArchivePage, PageHead } from "./parts";

const SOURCES: [string, string, string, string][] = [
  ["DLu/oscar_data", "https://github.com/DLu/oscar_data", "Every nomination and winner, ceremonies 1 to 98", "BSD 2-Clause"],
  ["TMDB", "https://www.themoviedb.org", "Posters, audience scores, gross, budget, language, country", "Non-commercial use, with credit"],
  ["Wikidata", "https://www.wikidata.org", "Birth years and gender, used for ages and totals", "CC0"],
  ["FRED, from BLS CPI-U", "https://fred.stlouisfed.org/series/CPIAUCNS", "Inflation adjustment to 2025 dollars", "US public data"],
  ["Wikipedia", "https://en.wikipedia.org", "Guild, BAFTA, Globe and Critics Choice winners, for the forecast", "Facts drawn from CC BY-SA pages"],
];

export default function MethodsPage() {
  return (
    <ArchivePage title="Methods">
      <PageHead title="Methods">
        <p>Where every number comes from, what each one means, and what it can’t tell you.</p>
      </PageHead>
      <div className="sheet methods">
        <section className="methods-wide">
          <h2>Sources</h2>
          <table className="methods-table">
            <thead>
              <tr>
                <th scope="col">Source</th>
                <th scope="col">What it provides</th>
                <th scope="col">Terms</th>
              </tr>
            </thead>
            <tbody>
              {SOURCES.map(([name, href, provides, terms]) => (
                <tr key={name}>
                  <th scope="row">
                    <a href={href} rel="noreferrer">
                      {name}
                    </a>
                  </th>
                  <td>{provides}</td>
                  <td>{terms}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="tmdb-credit">
            <img src="/credits/tmdb.svg" alt="TMDB" width={110} height={14} />
            <p>This product uses the TMDB API but is not endorsed or certified by TMDB.</p>
          </div>
        </section>

        <section>
          <h2>What counts</h2>
          <ul>
            <li>Nominations and wins mean competitive categories. Honorary and Scientific and Technical awards appear on Archive pages as honors and don’t count toward totals.</li>
            <li>82 entries the source marks as not official nominations don’t count either. They are write-ins, withdrawn entries and preliminary lists. The Archive still shows them, labeled, with the source’s note.</li>
            <li>Ceremony 2 announced no nominees, so its winners count as wins, and it is left out of comparisons between a winner and its field.</li>
            <li>A film counts once per nomination, so two acting nominations for one film count as two.</li>
          </ul>
        </section>

        <section>
          <h2>Definitions</h2>
          <ul>
            <li>Years are film years, not ceremony years. Early seasons such as 1927/28 span two.</li>
            <li>Age is film year minus birth year, so it can be off by one.</li>
            <li>Money is TMDB’s lifetime worldwide gross, adjusted for inflation by the film’s release year on story charts and shown unadjusted on film pages. Medians use Best Picture winners only.</li>
            <li>Audience scores are TMDB’s. A ceremony is compared only when every nominee has at least 50 votes, and tied scores share the better rank.</li>
            <li>Women’s share counts nominee credits with a recorded gender, in a two-way split. Non-binary nominees and people without gender data are left out of that split, not counted as either.</li>
          </ul>
        </section>

        <section>
          <h2>What this can’t tell you</h2>
          <ul>
            <li>TMDB’s money figures are entered by its community. Coverage falls below half before 1950, and some old entries look too low. Re-releases inflate old totals, so compare eras rather than single old films.</li>
            <li>Streaming films report little or no box office, and the pandemic closed theaters, so money figures from 2020 on overstate the shift.</li>
            <li>Audience scores come from people voting now, not in the year of release, and winning may lift a score. They show agreement, not cause.</li>
            <li>There is no race or ethnicity analysis here. The available sources rely on third-party classification of individuals that this project can’t audit.</li>
            <li>Gender and birth years come from Wikidata and are used for totals and ages. Person pages show birth years only.</li>
          </ul>
        </section>

        <section>
          <h2>The forecast</h2>
          <ul>
            <li>It is a conditional logit, a regression where each category’s odds add up to 100%, fitted on films since 1995. Each backtest year uses only earlier years.</li>
            <li>Precursor winners are read from Wikipedia’s award pages, matched to nominees by name, and spot-checked against Wikidata.</li>
            <li>BAFTA is left out before films of 2000, when it was held after the Oscars. Its results would leak the answer.</li>
            <li>A precursor only counts in its matching Oscar category, so an actor who won a supporting award and was nominated for a lead gets no credit for it.</li>
          </ul>
        </section>

        <section>
          <h2>How it’s checked</h2>
          <ul>
            <li>Every build fails if a known record stops matching, such as Titanic’s 14 nominations and 11 wins.</li>
            <li>Winners in the top four categories at ten random ceremonies were checked against Wikipedia’s ceremony pages.</li>
            <li>Every story claim is recomputed from the data before it’s written.</li>
          </ul>
        </section>

        <section>
          <h2>The small print</h2>
          <p>
            Every Envelope is an independent, non-commercial project. It is not affiliated with or endorsed by the Academy of Motion Picture Arts and Sciences. “Oscar” and “Academy
            Awards” are the Academy’s trademarks and are used only to describe the subject.
          </p>
        </section>
      </div>
    </ArchivePage>
  );
}
