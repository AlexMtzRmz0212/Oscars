"""Turn the raw nominations file into clean ceremonies, categories, films, people and nominations.

Each source quirk handled here has a matching test in tests/test_normalize.py.
"""
import csv
import re
import unicodedata
from collections import Counter, defaultdict

from common import AWARDS_FILE, NORMALIZED_FILE, write_json

NON_COMPETITIVE_CLASSES = {"SciTech", "Special"}
UNOFFICIAL_MARKER = "NOT AN OFFICIAL NOMINATION"
MULTI_SEPARATOR = "|"

# Canonical category -> family. Unmapped competitive categories fail the build, so a
# category new to the source can't silently fall out of the family charts.
COMPETITIVE_FAMILIES = {
    "BEST PICTURE": "Picture",
    "UNIQUE AND ARTISTIC PICTURE": "Picture",
    "DIRECTING": "Directing",
    "DIRECTING (Comedy Picture)": "Directing",
    "DIRECTING (Dramatic Picture)": "Directing",
    "ASSISTANT DIRECTOR": "Directing",
    "ACTOR IN A LEADING ROLE": "Acting",
    "ACTOR IN A SUPPORTING ROLE": "Acting",
    "ACTRESS IN A LEADING ROLE": "Acting",
    "ACTRESS IN A SUPPORTING ROLE": "Acting",
    "WRITING (Adapted Screenplay)": "Writing",
    "WRITING (Original Screenplay)": "Writing",
    "WRITING (Original Story)": "Writing",
    "WRITING (Title Writing)": "Writing",
    "CINEMATOGRAPHY": "Cinematography",
    "CINEMATOGRAPHY (Black-and-White)": "Cinematography",
    "CINEMATOGRAPHY (Color)": "Cinematography",
    "ART DIRECTION": "Design",
    "ART DIRECTION (Black-and-White)": "Design",
    "ART DIRECTION (Color)": "Design",
    "COSTUME DESIGN": "Design",
    "COSTUME DESIGN (Black-and-White)": "Design",
    "COSTUME DESIGN (Color)": "Design",
    "MAKEUP AND HAIRSTYLING": "Design",
    "FILM EDITING": "Editing",
    "CASTING": "Casting",
    "SOUND EDITING": "Sound",
    "SOUND MIXING": "Sound",
    "SOUND RECORDING": "Sound",
    "VISUAL EFFECTS": "Visual Effects",
    "MUSIC (Original Score)": "Music",
    "MUSIC (Original Song Score or Adaptation Score)": "Music",
    "MUSIC (Original Song)": "Music",
    "DANCE DIRECTION": "Music",
    "ANIMATED FEATURE FILM": "Animated Feature",
    "DOCUMENTARY (Feature)": "Documentary",
    "DOCUMENTARY (Short Subject)": "Documentary",
    "INTERNATIONAL FEATURE FILM": "International",
    "SHORT FILM (Animated)": "Shorts",
    "SHORT FILM (Live Action)": "Shorts",
    "SHORT SUBJECT (Color)": "Shorts",
    "SHORT SUBJECT (Comedy)": "Shorts",
    "SHORT SUBJECT (Novelty)": "Shorts",
    "SHORT SUBJECT (One-reel)": "Shorts",
    "SHORT SUBJECT (Two-reel)": "Shorts",
}
NON_COMPETITIVE_FAMILIES = {"SciTech": "Sci-Tech", "Special": "Honorary"}


def slugify(text):
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def read_rows(path=AWARDS_FILE):
    """The file is tab-separated despite its upstream name, rows drop trailing empty columns,
    and quotes inside a field are backslash-escaped."""
    with open(path, encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source, delimiter="\t", restval="", escapechar="\\"))


def parse_winner(value):
    if value == "True":
        return True
    if value == "":
        return False
    raise ValueError(f"Unexpected Winner value: {value!r}")


def entity_type(entity_id):
    if entity_id.startswith("nm"):
        return "person"
    if entity_id.startswith("co"):
        return "company"
    if entity_id.startswith("unk-"):
        return "unknown"
    raise ValueError(f"Unexpected nominee id: {entity_id!r}")


def split_multi(value):
    return value.split(MULTI_SEPARATOR) if value else []


def parse_nominees(row):
    """Pair nominee ids with names. `?` is a shared placeholder, so it gets a per-name id."""
    names = split_multi(row["Nominees"]) or split_multi(row["Name"])
    ids = split_multi(row["NomineeIds"])
    if ids and len(ids) != len(names):
        raise ValueError(f"Nominee name and id counts differ: {row['Nominees']!r} / {row['NomineeIds']!r}")

    nominees = []
    for index, name in enumerate(names):
        raw_id = ids[index] if ids else "?"
        entity_id = f"unk-{slugify(name)}" if raw_id == "?" else raw_id
        nominees.append({"id": entity_id, "name": name, "type": entity_type(entity_id)})
    return nominees


def parse_films(row):
    titles = split_multi(row["Film"])
    ids = split_multi(row["FilmId"])
    if ids and len(ids) != len(titles):
        raise ValueError(f"Film title and id counts differ: {row['Film']!r} / {row['FilmId']!r}")
    return [
        {"id": ids[index] if ids else f"unk-{slugify(title)}", "title": title}
        for index, title in enumerate(titles)
    ]


def category_family(row):
    if row["Class"] in NON_COMPETITIVE_CLASSES:
        return NON_COMPETITIVE_FAMILIES[row["Class"]]
    try:
        return COMPETITIVE_FAMILIES[row["CanonicalCategory"]]
    except KeyError:
        raise ValueError(f"No family for category: {row['CanonicalCategory']!r}") from None


def is_unofficial(row, winner):
    """Write-ins, withdrawn entries and preliminary lists are on the record but aren't nominations.

    Winners stay counted: at ceremony 2 the same note covers real winners, because the Academy
    announced no nominee list that year.
    """
    return UNOFFICIAL_MARKER in row["Note"].upper() and not winner


def parse_nomination(row):
    winner = parse_winner(row["Winner"])
    unofficial = is_unofficial(row, winner)
    in_competitive_category = row["Class"] not in NON_COMPETITIVE_CLASSES
    return {
        "ceremony": int(row["Ceremony"]),
        "year": row["Year"],
        "class": row["Class"],
        "category": row["CanonicalCategory"],
        "rawCategory": row["Category"],
        "family": category_family(row),
        "inCompetitiveCategory": in_competitive_category,
        "competitive": in_competitive_category and not unofficial,
        "unofficial": unofficial,
        "winner": winner,
        "films": parse_films(row),
        "nominees": parse_nominees(row),
        "credit": row["Name"],
        "detail": row["Detail"],
        "note": row["Note"],
        "citation": row["Citation"],
    }


def most_common(counter):
    """Most frequent spelling, alphabetical on ties, so builds are deterministic."""
    return min(counter, key=lambda value: (-counter[value], value))


def build_entities(nominations, key, label_key, extra=None):
    """Roll competitive nominations and wins up per film or per nominee."""
    labels = defaultdict(Counter)
    stats = defaultdict(lambda: {"nominations": 0, "wins": 0, "honors": 0, "ceremonies": set()})

    for nomination in nominations:
        for item in nomination[key]:
            labels[item["id"]][item[label_key]] += 1
            entry = stats[item["id"]]
            entry["ceremonies"].add(nomination["ceremony"])
            if nomination["unofficial"]:
                continue
            if not nomination["competitive"]:
                entry["honors"] += 1
                continue
            entry["nominations"] += 1
            entry["wins"] += nomination["winner"]

    entities = []
    for entity_id, entry in sorted(stats.items()):
        ceremonies = sorted(entry["ceremonies"])
        entity = {
            "id": entity_id,
            label_key: most_common(labels[entity_id]),
            "nominations": entry["nominations"],
            "wins": entry["wins"],
            "honors": entry["honors"],
            "firstCeremony": ceremonies[0],
            "lastCeremony": ceremonies[-1],
        }
        if extra:
            entity.update(extra(entity_id))
        entities.append(entity)
    return entities


def build_categories(nominations):
    by_category = {}
    for nomination in nominations:
        entry = by_category.setdefault(
            nomination["category"],
            {
                "slug": slugify(nomination["category"]),
                "name": nomination["category"],
                "family": nomination["family"],
                "class": nomination["class"],
                "competitive": nomination["inCompetitiveCategory"],
                "ceremonies": set(),
            },
        )
        entry["ceremonies"].add(nomination["ceremony"])

    categories = []
    for entry in by_category.values():
        ceremonies = sorted(entry.pop("ceremonies"))
        categories.append({**entry, "firstCeremony": ceremonies[0], "lastCeremony": ceremonies[-1], "ceremonyCount": len(ceremonies)})
    return sorted(categories, key=lambda category: (category["firstCeremony"], category["name"]))


def build_ceremonies(nominations):
    by_ceremony = defaultdict(lambda: {"year": "", "categories": set(), "nominations": 0})
    for nomination in nominations:
        entry = by_ceremony[nomination["ceremony"]]
        entry["year"] = nomination["year"]
        entry["nominations"] += 1
        if nomination["inCompetitiveCategory"]:
            entry["categories"].add(nomination["category"])
    return [
        {
            "ceremony": number,
            "filmYear": entry["year"],
            "competitiveCategories": len(entry["categories"]),
            "nominations": entry["nominations"],
        }
        for number, entry in sorted(by_ceremony.items())
    ]


def normalize(rows):
    nominations = [parse_nomination(row) for row in rows]
    film_years = defaultdict(list)
    for nomination in nominations:
        for film in nomination["films"]:
            film_years[film["id"]].append(nomination["year"])

    return {
        "ceremonies": build_ceremonies(nominations),
        "categories": build_categories(nominations),
        "films": build_entities(nominations, "films", "title", lambda film_id: {"filmYear": min(film_years[film_id])}),
        "people": build_entities(nominations, "nominees", "name", lambda entity_id: {"type": entity_type(entity_id)}),
        "nominations": nominations,
    }


def run():
    rows = read_rows()
    data = normalize(rows)
    write_json(NORMALIZED_FILE, data)
    print(
        f"  {len(rows)} rows: {len(data['ceremonies'])} ceremonies, {len(data['categories'])} categories, "
        f"{len(data['films'])} films, {len(data['people'])} nominees"
    )
    return data


if __name__ == "__main__":
    run()
