"""Stream IMDb's bulk files and keep only the films and people in the awards data.

The files are too large to keep (hundreds of MB), so nothing is stored but the filtered result.
IMDb's terms: personal and non-commercial use. See https://data.imdb.com/non-commercial-datasets/
"""
import csv
import gzip
import io
import urllib.request

from common import ENRICH, NORMALIZED_FILE, USER_AGENT, read_json, write_json

BASE_URL = "https://datasets.imdbws.com"
MISSING = "\\N"


def clean(value):
    return None if value == MISSING else value


def to_int(value):
    value = clean(value)
    return int(value) if value is not None and value.isdigit() else None


def read_rows(text_stream):
    """IMDb's files use no quoting at all, so quote handling must stay off."""
    return csv.DictReader(text_stream, delimiter="\t", quoting=csv.QUOTE_NONE)


def film_basics(row):
    genres = clean(row["genres"])
    return {
        "titleType": row["titleType"],
        "startYear": to_int(row["startYear"]),
        "runtime": to_int(row["runtimeMinutes"]),
        "genres": genres.split(",") if genres else [],
    }


def film_rating(row):
    return {"rating": float(row["averageRating"]), "votes": int(row["numVotes"])}


def person_basics(row):
    return {"birthYear": to_int(row["birthYear"]), "deathYear": to_int(row["deathYear"])}


def stream(filename, key, wanted, parse, into):
    url = f"{BASE_URL}/{filename}"
    print(f"  streaming {filename}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        with gzip.GzipFile(fileobj=response) as unzipped:
            text = io.TextIOWrapper(unzipped, encoding="utf-8", newline="")
            for row in read_rows(text):
                if row[key] in wanted:
                    into.setdefault(row[key], {}).update(parse(row))


def run():
    data = read_json(NORMALIZED_FILE)
    film_ids = {film["id"] for film in data["films"] if film["id"].startswith("tt")}
    person_ids = {person["id"] for person in data["people"] if person["id"].startswith("nm")}

    films, people = {}, {}
    stream("title.basics.tsv.gz", "tconst", film_ids, film_basics, films)
    stream("title.ratings.tsv.gz", "tconst", film_ids, film_rating, films)
    stream("name.basics.tsv.gz", "nconst", person_ids, person_basics, people)
    write_json(ENRICH / "imdb.json", {"films": films, "people": people})
    print(f"  matched {len(films)} of {len(film_ids)} films, {len(people)} of {len(person_ids)} people")


if __name__ == "__main__":
    run()
