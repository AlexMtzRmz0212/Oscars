"""Merge IMDb, TMDb and Wikidata into the normalized films and people.

Source files live in data/enrich and stay out of git: TMDb bars sharing cached datasets and caps
caching at 6 months, and IMDb bars republishing its data. Without them a build still runs, without posters.
Companies and placeholder ids are left unenriched on purpose.

Published values come from TMDb and Wikidata only. IMDb stays under each film's "private" key for
cross-checks in analysis/, and helps pick between conflicting Wikidata birth dates. story.py must never
publish anything under "private".
"""
import csv

from common import DATA, ENRICH, NORMALIZED_FILE, read_json, write_json

CPI_FILE = DATA / "reference" / "cpi_u_annual.csv"
CPI_BASE_YEAR = 2025
GENDER_NAMES = {"male": "man", "cisgender male": "man", "female": "woman", "cisgender female": "woman", "trans woman": "woman", "trans man": "man"}


def load_sources():
    """Returns None when enrichment hasn't been downloaded, so core builds still work."""
    paths = {name: ENRICH / f"{name}.json" for name in ("imdb", "tmdb", "wikidata")}
    if not all(path.exists() for path in paths.values()):
        return None
    return {name: read_json(path) for name, path in paths.items()}


def merge_film(film, imdb, tmdb):
    from_imdb = imdb.get(film["id"], {})
    from_tmdb = tmdb.get(film["id"], {})
    return {
        **film,
        "private": {
            "titleType": from_imdb.get("titleType"),
            "imdbRating": from_imdb.get("rating"),
            "imdbVotes": from_imdb.get("votes"),
        },
        "rating": from_tmdb.get("rating"),
        "votes": from_tmdb.get("votes"),
        "runtime": from_tmdb.get("runtime"),
        "genres": from_tmdb.get("genres", []),
        "poster": from_tmdb.get("poster"),
        "language": from_tmdb.get("language"),
        "releaseDate": from_tmdb.get("releaseDate"),
        "budget": from_tmdb.get("budget"),
        "revenue": from_tmdb.get("revenue"),
        "countries": from_tmdb.get("countries", []),
        "companies": from_tmdb.get("companies", []),
    }


def choose_birth_date(dates, imdb_year):
    """Wikidata can hold several dates. Prefer the one agreeing with IMDb, otherwise the earliest."""
    if not dates:
        return None
    for date in dates:
        if imdb_year and int(date[:4]) == imdb_year:
            return date
    return dates[0]


def choose_gender(genders):
    """Several values can't be reduced to one, so they stay out of the two-way aggregates."""
    if len(genders) != 1:
        return None
    return GENDER_NAMES.get(genders[0].lower())


def merge_person(person, imdb, wikidata):
    if person["type"] != "person":
        return person
    from_imdb = imdb.get(person["id"], {})
    from_wiki = wikidata.get(person["id"], {})
    birth_date = choose_birth_date(from_wiki.get("birthDates", []), from_imdb.get("birthYear"))
    return {
        **person,
        "birthDate": birth_date,
        "birthYear": int(birth_date[:4]) if birth_date else None,
        "gender": choose_gender(from_wiki.get("genders", [])),
        "birthCountries": from_wiki.get("countries", []),
    }


def load_cpi(path=CPI_FILE):
    with open(path, encoding="utf-8", newline="") as handle:
        return {int(row["year"]): float(row["cpi_u"]) for row in csv.DictReader(handle)}


def adjust_for_inflation(amount, year, cpi, base_year=CPI_BASE_YEAR):
    if amount is None or year not in cpi or base_year not in cpi:
        return None
    return amount * cpi[base_year] / cpi[year]


def run():
    sources = load_sources()
    if sources is None:
        print("  no enrichment files in data/enrich, skipping")
        return
    data = read_json(NORMALIZED_FILE)
    data["films"] = [merge_film(film, sources["imdb"]["films"], sources["tmdb"]) for film in data["films"]]
    data["people"] = [merge_person(person, sources["imdb"]["people"], sources["wikidata"]) for person in data["people"]]
    data["enriched"] = True
    write_json(NORMALIZED_FILE, data)


if __name__ == "__main__":
    run()
