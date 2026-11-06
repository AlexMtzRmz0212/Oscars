"""Fail the build when the normalized data breaks an invariant or a known record."""
import csv
from collections import Counter

from common import DATA, FIXTURES, NORMALIZED_FILE, read_json

EXPECTED_CEREMONIES = 98

# Records checked against published history, independent of the source file.
# (film id, title, nominations, wins)
FILM_RECORDS = [
    ("tt0052618", "Ben-Hur", 12, 11),
    ("tt0120338", "Titanic", 14, 11),
    ("tt0167260", "The Lord of the Rings: The Return of the King", 11, 11),
    ("tt0026174", "Captain Blood", 2, 0),
    ("tt0042192", "All about Eve", 14, 6),
    ("tt3783958", "La La Land", 14, 6),
    ("tt31193180", "Sinners", 16, 4),
]
# (person id, name, nominations, wins)
PEOPLE_RECORDS = [
    ("nm0002354", "John Williams", 54, 5),
    ("nm0000370", "Walt Disney", 59, 22),
    ("nm0000658", "Meryl Streep", 21, 3),
    ("nm0000031", "Katharine Hepburn", 12, 4),
    ("nm0005534", "Diane Warren", 17, 0),
    ("nm0002353", "Thomas Newman", 15, 0),
]
# (film id, title, release year, original language)
ENRICHED_FILMS = [
    ("tt0120338", "Titanic", 1997, "en"),
    ("tt0052618", "Ben-Hur", 1959, "en"),
    ("tt0167260", "The Return of the King", 2003, "en"),
]
# (award, film year, winning id, what the row proves)
PRECURSOR_RECORDS = [
    ("pga", 2013, "tt1454468", "tied, Gravity"),
    ("pga", 2013, "tt2024544", "tied, 12 Years a Slave"),
    ("gg_drama", 2019, "tt8579674", "the film 1917, whose title looks like a year"),
    ("bafta_film", 2016, "tt3783958", "La La Land, whose page wraps years in a template"),
    ("sag_cast", 2014, "tt2562232", "Birdman, named in short on the award page"),
    ("gg_director", 2015, "nm0327944", "Inarritu, with a written-out middle name"),
    ("dga", 2012, "tt1024648", "Argo reaches Best Picture though Ben Affleck wasn't nominated for Director"),
    ("sag_cast", 2024, "tt20215234", "Conclave, against the night's other favorites"),
]
# Famous cases where a precursor winner must not be credited.
PRECURSOR_NON_RECORDS = [
    ("sag_supporting_actress", 2008, "nm0000701", "Kate Winslet won in supporting but was an Oscar lead nominee"),
]
PRECURSOR_FILE = DATA / "precursors" / "wins.csv"
# (person id, name, birth year, gender)
ENRICHED_PEOPLE = [
    ("nm0000031", "Katharine Hepburn", 1907, "woman"),
    ("nm0000658", "Meryl Streep", 1949, "woman"),
    ("nm0002354", "John Williams", 1932, "man"),
]


def check_ceremonies(data):
    numbers = [ceremony["ceremony"] for ceremony in data["ceremonies"]]
    if numbers != list(range(1, EXPECTED_CEREMONIES + 1)):
        yield f"Expected ceremonies 1 to {EXPECTED_CEREMONIES}, found {len(numbers)}"


def check_best_picture(data):
    winners = Counter(
        nomination["ceremony"]
        for nomination in data["nominations"]
        if nomination["category"] == "BEST PICTURE" and nomination["winner"]
    )
    for ceremony in data["ceremonies"]:
        count = winners[ceremony["ceremony"]]
        if count != 1:
            yield f"Ceremony {ceremony['ceremony']} has {count} Best Picture winners"


def check_winner_links(data):
    """Every winner needs a film or nominee. An honor may instead name its recipient only in
    its citation: ceremony 86 went "to all those who built and operated film laboratories"."""
    for nomination in data["nominations"]:
        if not nomination["winner"] or nomination["films"] or nomination["nominees"]:
            continue
        if nomination["competitive"] or not nomination["citation"]:
            yield f"Winner with no film or nominee: ceremony {nomination['ceremony']}, {nomination['category']}"


def check_placeholder_ids(data):
    for person in data["people"]:
        if person["id"] == "?":
            yield "Placeholder id ? reached the people table"
    for nomination in data["nominations"]:
        for nominee in nomination["nominees"]:
            if nominee["id"] == "?":
                yield f"Placeholder id ? on nomination: ceremony {nomination['ceremony']}, {nomination['category']}"


def check_records(data):
    films = {film["id"]: film for film in data["films"]}
    people = {person["id"]: person for person in data["people"]}
    for table, records, label in ((films, FILM_RECORDS, "title"), (people, PEOPLE_RECORDS, "name")):
        for entity_id, name, nominations, wins in records:
            entity = table.get(entity_id)
            if entity is None:
                yield f"Record holder missing: {name} ({entity_id})"
            elif entity[label] != name or entity["nominations"] != nominations or entity["wins"] != wins:
                yield (
                    f"Record mismatch for {name}: expected {nominations} nominations and {wins} wins, "
                    f"found {entity[label]} with {entity['nominations']} and {entity['wins']}"
                )


def check_spot_checks(data):
    """Compare against winners confirmed from Wikipedia's ceremony pages."""
    fixture = FIXTURES / "spot_check.json"
    if not fixture.exists():
        yield f"Missing spot-check fixture: {fixture.name}"
        return

    winners = {}
    for nomination in data["nominations"]:
        if nomination["winner"]:
            names = {film["title"] for film in nomination["films"]} | {nominee["name"] for nominee in nomination["nominees"]}
            winners.setdefault((nomination["ceremony"], nomination["category"]), set()).update(names)

    for check in read_json(fixture):
        found = winners.get((check["ceremony"], check["category"]), set())
        if check["winner"] not in found:
            yield f"Spot check failed: ceremony {check['ceremony']}, {check['category']}: expected {check['winner']}, found {sorted(found)}"


def check_enrichment(data):
    """A bad join would look plausible on a chart, so test it against facts that can't drift."""
    if not data.get("enriched"):
        return

    films = {film["id"]: film for film in data["films"]}
    for film_id, title, year, language in ENRICHED_FILMS:
        film = films[film_id]
        if not film.get("poster") or film.get("language") != language or not film.get("rating"):
            yield f"Enrichment mismatch for {title}: {film.get('language')}, poster {film.get('poster')}, rating {film.get('rating')}"
        if not str(film.get("releaseDate") or "").startswith(str(year)):
            yield f"Release date mismatch for {title}: {film.get('releaseDate')}"

    people = {person["id"]: person for person in data["people"]}
    for person_id, name, birth_year, gender in ENRICHED_PEOPLE:
        person = people[person_id]
        if person.get("birthYear") != birth_year or person.get("gender") != gender:
            yield f"Enrichment mismatch for {name}: {person.get('birthYear')}, {person.get('gender')}"

    for film in data["films"]:
        rating = film.get("rating")
        if rating is not None and not 1 <= rating <= 10:
            yield f"Rating out of range for {film['title']}: {rating}"
        for field in ("budget", "revenue"):
            if film.get(field) is not None and film[field] <= 0:
                yield f"{field} not positive for {film['title']}: {film[field]}"


def check_precursors(data):
    """A shape check on every award year, plus results that are easy to get wrong."""
    if not PRECURSOR_FILE.exists():
        return
    with open(PRECURSOR_FILE, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    found = {(row["award"], int(row["film_year"]), row["id"]) for row in rows}
    for award, year, entity, why in PRECURSOR_RECORDS:
        if (award, year, entity) not in found:
            yield f"Precursor record missing: {award} {year}, {why}"
    for award, year, entity, why in PRECURSOR_NON_RECORDS:
        if (award, year, entity) in found:
            yield f"Precursor wrongly matched: {award} {year}, {why}"
    known = {entity["id"] for entity in [*data["films"], *data["people"]]}
    for row in rows:
        if row["id"] not in known:
            yield f"Precursor winner isn't in the record: {row['award']} {row['film_year']} {row['id']}"


CHECKS = [check_ceremonies, check_best_picture, check_winner_links, check_placeholder_ids, check_records, check_spot_checks, check_enrichment, check_precursors]


def collect_errors(data):
    return [error for check in CHECKS for error in check(data)]


def run():
    errors = collect_errors(read_json(NORMALIZED_FILE))
    if errors:
        for error in errors:
            print(f"  FAIL {error}")
        raise SystemExit(f"Validation failed with {len(errors)} errors")
    print(f"  all {len(CHECKS)} checks passed")


if __name__ == "__main__":
    run()
