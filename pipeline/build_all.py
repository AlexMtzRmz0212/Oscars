"""Run the whole build, stopping at the first failure.

Enrichment sources in data/enrich are downloaded separately, with fetch_imdb.py, fetch_tmdb.py,
fetch_wikidata.py and fetch_cpi.py, because they are slow and need a token. See the README.
"""
import coverage
import enrich
import explore
import fetch_awards
import normalize
import predict
import season
import story
import validate

STEPS = [
    ("Fetching awards", fetch_awards.run),
    ("Normalizing", normalize.run),
    ("Enriching", enrich.run),
    ("Validating", validate.run),
    ("Reporting coverage", coverage.run),
    ("Building story data", story.run),
    ("Building the Archive", explore.run),
    ("Backtesting the model", predict.run),
    ("Building the 99th season", season.run),
]


def main():
    for label, step in STEPS:
        print(label)
        step()
    print("Done")


if __name__ == "__main__":
    main()
