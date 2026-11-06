# Every Envelope

A data history of the Academy Awards, staged as one night at a grand theatre: a scroll-driven story up front, then a searchable archive of every ceremony, film, person, studio and category.

Independent and non-commercial. Not affiliated with or endorsed by the Academy of Motion Picture Arts and Sciences.

## Run it

`public/data/` and `data/enrich/` stay out of git (see [Source terms](#source-terms)), so a fresh checkout needs the data built first.

1. Copy `.env.example` to `.env.local` and add a TMDb token.
2. Download the enrichment data, about 15 minutes, from `pipeline/`:

   ```bash
   python fetch_imdb.py
   python fetch_tmdb.py
   python fetch_wikidata.py
   python fetch_cpi.py
   ```

3. Build the data and start the site:

   ```bash
   npm install
   npm run data
   npm run dev
   ```

Or double-click `DEV.bat` once the data exists. The site runs at <http://localhost:5177>.

## Data pipeline

`pipeline/` is Python with the standard library only. The site reads only the precomputed files in `public/data/`.

| Step | Script | Output |
|---|---|---|
| Download, pinned by commit and hash | `fetch_awards.py` | `data/raw/oscars.tsv` |
| Clean and roll up | `normalize.py` | `data/build/normalized.json` |
| Merge film and person data | `enrich.py` | Adds to the same file |
| Check invariants and known records | `validate.py` | Fails the build on any error |
| Report completeness per era | `coverage.py` | `data/reports/coverage.md` |
| Precompute story charts | `story.py` | `public/data/story/*.json` |
| Build the Archive | `explore.py` | `public/data/{ceremonies,categories,films,people}/`, `search.json` |

| Backtest the model | `predict.py` | `public/data/season/backtest.json` |
| Build the 99th season | `season.py` | `public/data/season/season.json` |

```bash
npm run test:data
```

`data/fixtures/spot_check.json` holds 40 winners from 10 random ceremonies, confirmed against Wikipedia's ceremony pages.

## The story's claims

`analysis/story_claims.py` recomputes every planned claim into `analysis/story_claims.md`. `analysis/VERDICTS.md` records which claims the story may use and what each must also say. Rerun it after any data change, and update the copy if a number moves.

## The forecast

`pipeline/predict.py` is a conditional logit for six categories, in the standard library. Its backtest walks forward, so each year is predicted from earlier years only.

`pipeline/fetch_precursors.py` reads precursor winners from Wikipedia into `data/precursors/wins.csv`, and audits each award in `data/reports/precursors.md`. Its pages are cached in `data/cache/precursors/`.

**To run the 99th season, follow [data/season_99/README.md](data/season_99/README.md).** The key dates are nominations on Jan 21, the freeze on Mar 13 and the ceremony on Mar 14, 2027.

## Site map

| Route | Page |
|---|---|
| `/` | The Show |
| `/season` | The 99th: forecast and track record |
| `/ceremonies`, `/ceremonies/:n` | Every ceremony, and each night's full ballot |
| `/films/:id`, `/people/:id`, `/studios/:id` | A film's, person's or studio's record |
| `/categories`, `/categories/:slug` | Every category, and its winners by night |
| `/born/:year` | What won in a given year |
| `/methods` | Sources, definitions and caveats |

Press `/` anywhere to search.

## Deploying

Because `public/data/` isn't in git, Vercel can't rebuild it from the repo. Build locally, then deploy the result:

```bash
npm run data
npm run build
```

## Design rules

- Gold always means won. Dim ivory always means nominated. Red is never used for data.
- Charts sit on velvet black, the surface where the gold and ivory pair passes colour-blind separation checks.
- No statuette art or official Academy logos. Envelopes and curtains carry the identity.

## Source terms

- **TMDb:** non-commercial use with the notice line and logo. Caching is capped at 6 months, so **refresh TMDb data before May 2027**. Sharing cached datasets counts as commercial use, which is why its data stays out of git. The site's own data files are necessarily public once deployed.
- **IMDb:** its data must not be republished, so it's a private cross-check in `analysis/`. Nothing from IMDb's files reaches `public/data/`.
- **Wikidata:** CC0. Person pages show birth years only; gender is used in totals.

## Data credits

- Nominations: [DLu/oscar_data](https://github.com/DLu/oscar_data) (BSD 2-Clause)
- Posters, money, scores, runtimes and genres: [TMDB](https://www.themoviedb.org). This product uses the TMDB API but is not endorsed or certified by TMDB.
- Birth years and gender: [Wikidata](https://www.wikidata.org) (CC0)
- Inflation: US Bureau of Labor Statistics CPI-U, via [FRED](https://fred.stlouisfed.org/series/CPIAUCNS)
- Precursor winners: [Wikipedia](https://en.wikipedia.org)'s award pages (CC BY-SA)
