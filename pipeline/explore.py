"""Write the Archive's files: one per ceremony and category, shards for films and people, a search index.

Publishes awards, TMDb and birth years only. Never anything under a film's "private" key, and never a
person's gender or full birth date: those are used in aggregate in the story and aren't needed per person.
"""
import re
import shutil
from collections import Counter, defaultdict

from common import NORMALIZED_FILE, OUT, read_json, write_json
from normalize import UNOFFICIAL_MARKER, slugify
from story import FAMILY_ORDER, first_year

SHARD_COUNT = 100
LEADERBOARD_SIZE = 6
CO_NOMINEE_LIMIT = 8
FAMILY_RANK = {family: rank for rank, family in enumerate(FAMILY_ORDER)}
LOWERCASE_WORDS = {"a", "an", "and", "in", "of", "or", "the"}


def shard_of(entity_id):
    """Matches shardOf in src/lib/archive.ts. Ids are ASCII, so both languages agree on the sum."""
    return sum(ord(character) for character in entity_id) % SHARD_COUNT


def category_label(name):
    """BEST PICTURE to Best Picture. Text inside brackets is already written for reading."""
    match = re.match(r"^([^(]*)(\(.*\))?$", name)
    words = match.group(1).strip().split()
    titled = [word.capitalize() if index == 0 or word.lower() not in LOWERCASE_WORDS else word.lower() for index, word in enumerate(words)]
    return " ".join(titled) + (f" {match.group(2)}" if match.group(2) else "")


def clean_detail(detail):
    return detail.replace("|", ", ")


def clean_note(note):
    """Drops the source's NOTE: labels. Sci-Tech notes are engineering detail, covered by the citation."""
    parts = [part.removeprefix("NOTE:").strip() for part in note.split("|")]
    text = " ".join(part for part in parts if part)
    return re.sub(rf"{UNOFFICIAL_MARKER}\.?\s*", "", re.sub(r"THIS IS ", "", text, count=1) if UNOFFICIAL_MARKER in text else text).strip()


def nominee_view(nominee):
    return {"id": nominee["id"], "name": nominee["name"], "type": nominee["type"]}


def entry_view(nomination):
    """One nomination, as any Archive page shows it."""
    view = {
        "ceremony": nomination["ceremony"],
        "year": nomination["year"],
        "category": category_label(nomination["category"]),
        "slug": slugify(nomination["category"]),
        "competitive": nomination["inCompetitiveCategory"],
        "winner": nomination["winner"],
        "films": nomination["films"],
        "nominees": [nominee_view(nominee) for nominee in nomination["nominees"]],
    }
    if nomination["unofficial"]:
        view["unofficial"] = True
    if nomination["detail"]:
        view["detail"] = clean_detail(nomination["detail"])
    if nomination["note"] and nomination["inCompetitiveCategory"]:
        view["note"] = clean_note(nomination["note"])
    if nomination["citation"]:
        view["citation"] = nomination["citation"]
    return view


def film_card(film):
    return {"id": film["id"], "title": film["title"], "year": film["filmYear"], "poster": film.get("poster")}


def category_order(category, family):
    """Competitive first in programme order, with honors last."""
    return (FAMILY_RANK.get(family, len(FAMILY_ORDER)), category)


def build_ceremony_pages(data, films):
    by_ceremony = defaultdict(lambda: defaultdict(list))
    for nomination in data["nominations"]:
        by_ceremony[nomination["ceremony"]][nomination["category"]].append(nomination)

    pages, index = {}, []
    for ceremony in data["ceremonies"]:
        number = ceremony["ceremony"]
        groups = by_ceremony[number]
        ordered = sorted(groups, key=lambda name: category_order(name, groups[name][0]["family"]))
        categories = [
            {
                "name": category_label(name),
                "slug": slugify(name),
                "family": groups[name][0]["family"],
                "competitive": groups[name][0]["inCompetitiveCategory"],
                "entries": [entry_view(row) for row in sorted(groups[name], key=lambda row: not row["winner"])],
            }
            for name in ordered
        ]
        picture = next((row for row in groups.get("BEST PICTURE", []) if row["winner"]), None)
        best_picture = film_card(films[picture["films"][0]["id"]]) if picture else None
        pages[number] = {
            "ceremony": number,
            "year": ceremony["filmYear"],
            "competitiveCategories": ceremony["competitiveCategories"],
            "bestPicture": best_picture,
            "categories": categories,
        }
        index.append({"ceremony": number, "year": ceremony["filmYear"], "bestPicture": best_picture})
    return pages, index


def build_category_pages(data):
    by_category = defaultdict(list)
    for nomination in data["nominations"]:
        by_category[nomination["category"]].append(nomination)

    pages, index = {}, []
    for category in data["categories"]:
        rows = by_category[category["name"]]
        nights = defaultdict(list)
        for row in rows:
            nights[row["ceremony"]].append(row)

        wins, nominations, names, types = Counter(), Counter(), {}, {}
        for row in rows:
            for nominee in row["nominees"]:
                if nominee["type"] == "unknown" or row["unofficial"]:
                    continue
                nominations[nominee["id"]] += 1
                wins[nominee["id"]] += row["winner"]
                names[nominee["id"]] = nominee["name"]
                types[nominee["id"]] = nominee["type"]
        leaders = sorted(nominations, key=lambda entity: (-wins[entity], -nominations[entity], names[entity]))[:LEADERBOARD_SIZE]

        slug = category["slug"]
        label = category_label(category["name"])
        pages[slug] = {
            "slug": slug,
            "name": label,
            "family": category["family"],
            "competitive": category["competitive"],
            "firstCeremony": category["firstCeremony"],
            "lastCeremony": category["lastCeremony"],
            "ceremonyCount": category["ceremonyCount"],
            "nights": [
                {
                    "ceremony": number,
                    "year": nights[number][0]["year"],
                    "nominees": sum(not row["unofficial"] for row in nights[number]),
                    "winners": [entry_view(row) for row in nights[number] if row["winner"]],
                }
                for number in sorted(nights, reverse=True)
            ],
            "leaders": [{"id": entity, "name": names[entity], "type": types[entity], "wins": wins[entity], "nominations": nominations[entity]} for entity in leaders],
        }
        index.append({
            "slug": slug,
            "name": label,
            "family": category["family"],
            "competitive": category["competitive"],
            "firstCeremony": category["firstCeremony"],
            "lastCeremony": category["lastCeremony"],
        })
    index.sort(key=lambda row: category_order(row["name"], row["family"]))
    return pages, index


def film_ranks(data):
    """Each film's nomination rank among competitive nominees of its first ceremony, ties sharing a rank."""
    per_night = defaultdict(Counter)
    for nomination in data["nominations"]:
        if nomination["competitive"]:
            for film in nomination["films"]:
                per_night[nomination["ceremony"]][film["id"]] += 1

    ranks = {}
    for film in data["films"]:
        counts = per_night.get(film["firstCeremony"], Counter())
        mine = counts.get(film["id"], 0)
        if mine:
            ranks[film["id"]] = {"rank": 1 + sum(count > mine for count in counts.values()), "of": len(counts), "ceremony": film["firstCeremony"]}
    return ranks


def build_film_shards(data):
    entries = defaultdict(list)
    for nomination in data["nominations"]:
        for film in nomination["films"]:
            entries[film["id"]].append(entry_view(nomination))
    ranks = film_ranks(data)

    shards = defaultdict(dict)
    for film in data["films"]:
        shards[shard_of(film["id"])][film["id"]] = {
            **film_card(film),
            "nominations": film["nominations"],
            "wins": film["wins"],
            "honors": film["honors"],
            "rating": film.get("rating"),
            "votes": film.get("votes"),
            "runtime": film.get("runtime"),
            "genres": film.get("genres", []),
            "language": film.get("language"),
            "countries": film.get("countries", []),
            "budget": film.get("budget"),
            "revenue": film.get("revenue"),
            "rank": ranks.get(film["id"]),
            "entries": sorted(entries[film["id"]], key=lambda entry: (entry["ceremony"], not entry["winner"], entry["category"])),
        }
    return shards


def build_people_shards(data):
    entries = defaultdict(list)
    partners = defaultdict(Counter)
    names = {}
    for nomination in data["nominations"]:
        people = nomination["nominees"]
        for person in people:
            entries[person["id"]].append(entry_view(nomination))
            names[person["id"]] = person
            for other in people:
                if other["id"] != person["id"] and other["type"] != "unknown":
                    partners[person["id"]][other["id"]] += 1

    shards = defaultdict(dict)
    for person in data["people"]:
        person_id = person["id"]
        shards[shard_of(person_id)][person_id] = {
            "id": person_id,
            "name": person["name"],
            "type": person["type"],
            "nominations": person["nominations"],
            "wins": person["wins"],
            "honors": person["honors"],
            "birthYear": person.get("birthYear"),
            "firstCeremony": person["firstCeremony"],
            "lastCeremony": person["lastCeremony"],
            "partners": [
                {"id": other, "name": names[other]["name"], "type": names[other]["type"], "shared": count}
                for other, count in partners[person_id].most_common(CO_NOMINEE_LIMIT)
            ],
            "entries": sorted(entries[person_id], key=lambda entry: (entry["ceremony"], not entry["winner"], entry["category"])),
        }
    return shards


def build_search(data):
    """Compact rows for the search box: kind, id, name, a year and the counts that rank results."""
    rows = []
    for film in data["films"]:
        rows.append({"k": "film", "i": film["id"], "n": film["title"], "y": first_year(film["filmYear"]), "w": film["wins"], "c": film["nominations"]})
    for person in data["people"]:
        kind = {"person": "person", "unknown": "person", "company": "studio"}[person["type"]]
        rows.append({"k": kind, "i": person["id"], "n": person["name"], "w": person["wins"], "c": person["nominations"]})
    for category in data["categories"]:
        rows.append({"k": "category", "i": category["slug"], "n": category_label(category["name"]), "w": 0, "c": 0})
    for ceremony in data["ceremonies"]:
        rows.append({"k": "ceremony", "i": str(ceremony["ceremony"]), "n": f"Ceremony {ceremony['ceremony']}", "y": first_year(ceremony["filmYear"]), "w": 0, "c": 0})
    return rows


def run():
    data = read_json(NORMALIZED_FILE)
    films = {film["id"]: film for film in data["films"]}

    # Start clean, so a shard from an older build can't linger.
    for folder in ("ceremonies", "categories", "films", "people"):
        shutil.rmtree(OUT / folder, ignore_errors=True)

    ceremony_pages, ceremony_index = build_ceremony_pages(data, films)
    write_json(OUT / "ceremonies" / "index.json", ceremony_index)
    for number, page in ceremony_pages.items():
        write_quiet(OUT / "ceremonies" / f"{number}.json", page)

    category_pages, category_index = build_category_pages(data)
    write_json(OUT / "categories" / "index.json", category_index)
    for slug, page in category_pages.items():
        write_quiet(OUT / "categories" / f"{slug}.json", page)

    for number, shard in build_film_shards(data).items():
        write_quiet(OUT / "films" / f"{number:02d}.json", shard)
    for number, shard in build_people_shards(data).items():
        write_quiet(OUT / "people" / f"{number:02d}.json", shard)

    write_json(OUT / "search.json", build_search(data))
    print(f"  wrote {len(ceremony_pages)} ceremonies, {len(category_pages)} categories, {SHARD_COUNT} film and person shards")


def write_quiet(path, payload):
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    run()
