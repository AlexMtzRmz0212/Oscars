"""Precompute one small JSON file per story act. Competitive awards only, unless a file says otherwise.

Publishes TMDb, Wikidata and awards values only. Nothing under a film's "private" key may appear here.
"""
from collections import Counter, defaultdict
from statistics import median

from common import NORMALIZED_FILE, OUT, read_json, write_json
from enrich import adjust_for_inflation, load_cpi

# Keeps the crowded low-count cells from bloating the file; full lists belong to the Archive.
MAX_FILMS_PER_CELL = 30
ERAS = [("1927-49", 1927, 1949), ("1950-69", 1950, 1969), ("1970-89", 1970, 1989), ("1990-2009", 1990, 2009), ("2010-25", 2010, 2025)]
BEST_PICTURE = "BEST PICTURE"
DIRECTING = {"DIRECTING", "DIRECTING (Dramatic Picture)", "DIRECTING (Comedy Picture)"}
EDITING = {"FILM EDITING"}
SCREENPLAY = {"WRITING (Adapted Screenplay)", "WRITING (Original Screenplay)", "WRITING (Original Story)"}
LEAD_ACTOR = "ACTOR IN A LEADING ROLE"
LEAD_ACTRESS = "ACTRESS IN A LEADING ROLE"
ACTING = {LEAD_ACTOR, LEAD_ACTRESS, "ACTOR IN A SUPPORTING ROLE", "ACTRESS IN A SUPPORTING ROLE"}
CRAFTS = [
    ("Directing", {"DIRECTING"}),
    ("Cinematography", {"CINEMATOGRAPHY", "CINEMATOGRAPHY (Black-and-White)", "CINEMATOGRAPHY (Color)"}),
    ("Original Score", {"MUSIC (Original Score)"}),
    ("Writing", {"WRITING (Adapted Screenplay)", "WRITING (Original Screenplay)"}),
    ("Film Editing", {"FILM EDITING"}),
    ("Costume Design", {"COSTUME DESIGN", "COSTUME DESIGN (Black-and-White)", "COSTUME DESIGN (Color)"}),
]
FAMILY_ORDER = [
    "Picture", "Directing", "Acting", "Writing", "Cinematography", "Design", "Editing", "Sound",
    "Visual Effects", "Music", "Shorts", "Documentary", "International", "Animated Feature", "Casting",
]
# Scores with fewer votes than this are too thin to rank a nominee by.
MIN_AUDIENCE_VOTES = 50
# Careers drawn in Act VII: (person id, why they are in the story)
CAREERS = ["nm0002354", "nm0005534", "nm0002353"]
LEADERBOARD_SIZE = 8


def film_summary(film):
    return {"id": film["id"], "title": film["title"], "year": film["filmYear"], "poster": film.get("poster")}


def first_year(year_text):
    return int(year_text.split("/")[0])


def era_of(year):
    for name, start, end in ERAS:
        if start <= year <= end:
            return name
    raise ValueError(f"No era for {year}")


def share(part, whole):
    return round(part / whole, 3) if whole else None


def competitive_only(nominations):
    return [nomination for nomination in nominations if nomination["competitive"]]


def best_picture_by_ceremony(nominations):
    groups = defaultdict(list)
    for nomination in nominations:
        if nomination["category"] == BEST_PICTURE:
            groups[nomination["ceremony"]].append(nomination)
    return dict(sorted(groups.items()))


def build_meta(ceremonies):
    """Headline facts for the hero. Ceremony 1 covers 1927/28, so take the first year of a split."""
    return {
        "ceremonies": len(ceremonies),
        "firstFilmYear": first_year(ceremonies[0]["filmYear"]),
        "lastFilmYear": first_year(ceremonies[-1]["filmYear"]),
    }


def build_overture(nominations, ceremonies):
    """Every competitive nomination, as one point of light per nomination in its ceremony's column."""
    counts = defaultdict(lambda: [0, 0])
    for nomination in competitive_only(nominations):
        counts[nomination["ceremony"]][0] += 1
        counts[nomination["ceremony"]][1] += nomination["winner"]
    columns = [
        {"ceremony": ceremony["ceremony"], "year": ceremony["filmYear"], "nominations": counts[ceremony["ceremony"]][0], "wins": counts[ceremony["ceremony"]][1]}
        for ceremony in ceremonies
    ]
    return {
        "totals": {"nominations": sum(column["nominations"] for column in columns), "wins": sum(column["wins"] for column in columns)},
        "columns": columns,
    }


def build_programme(categories, nominations, ceremonies):
    """How many categories each family fielded each night."""
    per_family = defaultdict(lambda: defaultdict(set))
    for nomination in competitive_only(nominations):
        per_family[nomination["family"]][nomination["ceremony"]].add(nomination["category"])

    numbers = [ceremony["ceremony"] for ceremony in ceremonies]
    competitive = [category for category in categories if category["competitive"]]
    last = numbers[-1]
    totals = [ceremony["competitiveCategories"] for ceremony in ceremonies]
    peak_index = max(range(len(totals)), key=lambda index: totals[index])
    return {
        "ceremonies": [{"ceremony": ceremony["ceremony"], "year": ceremony["filmYear"], "total": ceremony["competitiveCategories"]} for ceremony in ceremonies],
        "families": [{"name": family, "counts": [len(per_family[family][number]) for number in numbers]} for family in FAMILY_ORDER],
        "facts": {
            "first": totals[0],
            "latest": totals[-1],
            "peak": totals[peak_index],
            "peakCeremony": numbers[peak_index],
            "peakYear": ceremonies[peak_index]["filmYear"],
            "everCategories": len(competitive),
            "retired": sum(category["lastCeremony"] < last for category in competitive),
        },
    }


def build_formula(nominations, films):
    """Each Best Picture winner, with what else it won and whether it led the nominations."""
    competitive = competitive_only(nominations)
    wins_by_film = defaultdict(set)
    nominations_per_night = defaultdict(Counter)
    for nomination in competitive:
        for film in nomination["films"]:
            nominations_per_night[nomination["ceremony"]][film["id"]] += 1
            if nomination["winner"]:
                wins_by_film[(nomination["ceremony"], film["id"])].add(nomination["category"])

    winners = []
    for ceremony, entries in best_picture_by_ceremony(competitive).items():
        winner = next(entry for entry in entries if entry["winner"])
        film_id = winner["films"][0]["id"]
        film = films[film_id]
        wins = set().union(*(wins_by_film[(ceremony, item["id"])] for item in winner["films"]))
        counts = nominations_per_night[ceremony]
        entrants = {item["id"] for entry in entries for item in entry["films"]}
        top = max(counts[entrant] for entrant in entrants)
        # Ceremony 2 announced no nominees, so its winner had no field to lead.
        contested = len(entrants) > 1
        winners.append({
            **film_summary(film),
            "ceremony": ceremony,
            "era": era_of(first_year(winner["year"])),
            "directing": bool(wins & DIRECTING),
            "editing": bool(wins & EDITING),
            "screenplay": bool(wins & SCREENPLAY),
            "acting": bool(wins & ACTING),
            "contested": contested,
            "mostNominated": contested and any(counts[item["id"]] == top for item in winner["films"]),
        })

    flags = ["directing", "editing", "screenplay", "acting"]

    def era_row(name):
        members = [entry for entry in winners if entry["era"] == name]
        contested = [entry for entry in members if entry["contested"]]
        return {
            "era": name,
            "winners": len(members),
            "mostNominated": share(sum(entry["mostNominated"] for entry in contested), len(contested)),
            **{flag: share(sum(entry[flag] for entry in members), len(members)) for flag in flags},
        }

    eras = [era_row(name) for name, _, _ in ERAS]
    flags = [*flags, "mostNominated"]
    return {"winners": winners, "eras": eras, "totals": {flag: sum(entry[flag] for entry in winners) for flag in flags}}


def build_money(nominations, films, cpi):
    """Best Picture nominees only, because revenue is too sparse elsewhere. Dollars are 2025 dollars."""
    nominees = []
    decades = defaultdict(lambda: {"winners": 0, "nominees": 0, "known": 0, "winnerValues": []})
    fully_known = []

    for ceremony, entries in best_picture_by_ceremony(competitive_only(nominations)).items():
        year = first_year(entries[0]["year"])
        decade = decades[year // 10 * 10]
        night = []
        complete = True
        for entry in entries:
            for item in entry["films"]:
                decade["nominees"] += 1
                decade["winners"] += entry["winner"]
                adjusted = adjust_for_inflation(films[item["id"]].get("revenue"), year, cpi)
                if adjusted is None:
                    complete = False
                    continue
                decade["known"] += 1
                if entry["winner"]:
                    decade["winnerValues"].append(adjusted)
                row = {"title": films[item["id"]]["title"], "year": year, "ceremony": ceremony, "winner": entry["winner"], "revenue": round(adjusted)}
                night.append(row)
                nominees.append(row)
        if complete and len(night) > 1:
            top = max(night, key=lambda row: row["revenue"])
            top["topGrosser"] = True
            fully_known.append({"ceremony": ceremony, "year": year, "topGrosserWon": top["winner"], "top": top["title"]})

    in_range = lambda start, end: [night for night in fully_known if start <= night["year"] <= end]  # noqa: E731
    twenty_tens = in_range(2010, 2019)
    return {
        "nominees": nominees,
        "decades": [
            {
                "decade": decade,
                "medianWinner": round(median(values["winnerValues"])) if values["winnerValues"] else None,
                "winnersKnown": len(values["winnerValues"]),
                "winners": values["winners"],
                "nomineesKnown": values["known"],
                "nominees": values["nominees"],
            }
            for decade, values in sorted(decades.items())
        ],
        "topGrosser": {
            "2010s": {"won": sum(night["topGrosserWon"] for night in twenty_tens), "ceremonies": len(twenty_tens)},
            "1990to2009": {"won": sum(night["topGrosserWon"] for night in in_range(1990, 2009)), "ceremonies": len(in_range(1990, 2009))},
        },
    }


def build_audience(nominations, films, min_votes=MIN_AUDIENCE_VOTES):
    """Where each Best Picture winner ranked among its field by TMDb audience score.

    A ceremony counts only when every nominee has a score with enough votes. Tied scores share the
    better rank, so a winner tied for the top counts as the audience's favourite.
    """
    nights = []
    for ceremony, entries in best_picture_by_ceremony(competitive_only(nominations)).items():
        field = [
            {"film": films[item["id"]], "winner": entry["winner"]}
            for entry in entries
            for item in entry["films"]
        ]
        if len(field) < 2:
            continue  # Ceremony 2 announced no nominees, so there is no field to rank.
        if not all(row["film"].get("rating") is not None and (row["film"].get("votes") or 0) >= min_votes for row in field):
            continue
        winner = next(row for row in field if row["winner"])
        favourite = max(field, key=lambda row: (row["film"]["rating"], row["film"]["votes"]))
        rank = 1 + sum(row["film"]["rating"] > winner["film"]["rating"] for row in field)
        year = first_year(entries[0]["year"])
        nights.append({
            "ceremony": ceremony,
            "year": year,
            "era": era_of(year),
            "size": len(field),
            "rank": rank,
            "winner": {**film_summary(winner["film"]), "rating": winner["film"]["rating"]},
            "favourite": {**film_summary(favourite["film"]), "rating": favourite["film"]["rating"]},
            "gap": round(favourite["film"]["rating"] - winner["film"]["rating"], 2),
        })

    ranks = Counter(night["rank"] for night in nights)
    return {
        "nights": nights,
        "ceremoniesCompared": len(nights),
        "ceremoniesTotal": len(best_picture_by_ceremony(nominations)),
        "chance": round(sum(1 / night["size"] for night in nights) / len(nights), 3) if nights else None,
        "ranks": [{"rank": rank, "ceremonies": ranks[rank]} for rank in sorted(ranks)],
        "eras": [
            {
                "era": name,
                "ceremonies": sum(night["era"] == name for night in nights),
                "favouriteWon": sum(night["era"] == name and night["rank"] == 1 for night in nights),
            }
            for name, _, _ in ERAS
        ],
        "widestGaps": sorted(nights, key=lambda night: -night["gap"])[:4],
    }


def build_gold(nominations, films, people):
    competitive = competitive_only(nominations)

    def winners_in(category):
        rows = []
        for nomination in competitive:
            if nomination["category"] != category or not nomination["winner"]:
                continue
            year = first_year(nomination["year"])
            for nominee in nomination["nominees"]:
                birth = people[nominee["id"]].get("birthYear")
                if birth is not None:
                    rows.append({"name": nominee["name"], "film": nomination["films"][0]["title"], "year": year, "age": year - birth})
        return sorted(rows, key=lambda row: (row["age"], row["year"]))

    def age_group(category):
        rows = winners_in(category)
        ages = [row["age"] for row in rows]
        return {"winners": rows, "mean": round(sum(ages) / len(ages), 1), "median": median(ages)}

    def era_gaps():
        gaps = []
        for era, start, end in ERAS:
            means = {}
            for key, category in (("actor", LEAD_ACTOR), ("actress", LEAD_ACTRESS)):
                ages = [row["age"] for row in winners_in(category) if start <= row["year"] <= end]
                means[key] = round(sum(ages) / len(ages), 1) if ages else None
            both = means["actor"] is not None and means["actress"] is not None
            gaps.append({"era": era, **means, "gap": round(means["actor"] - means["actress"], 1) if both else None})
        return gaps

    crafts = []
    for name, categories in CRAFTS:
        counts = defaultdict(Counter)
        for nomination in competitive:
            if nomination["category"] in categories:
                for nominee in nomination["nominees"]:
                    if nominee["type"] == "person":
                        counts[era_of(first_year(nomination["year"]))][people[nominee["id"]].get("gender")] += 1
        crafts.append({
            "craft": name,
            "eras": [
                {"era": era, "women": counts[era]["woman"], "known": counts[era]["woman"] + counts[era]["man"], "share": share(counts[era]["woman"], counts[era]["woman"] + counts[era]["man"])}
                for era, _, _ in ERAS
            ],
        })

    directing_women = [
        {"name": nominee["name"], "ceremony": nomination["ceremony"], "won": nomination["winner"]}
        for nomination in competitive
        if nomination["category"] == "DIRECTING"
        for nominee in nomination["nominees"]
        if people[nominee["id"]].get("gender") == "woman"
    ]

    language = {"nominees": 0, "nonEnglish": 0, "byEra": Counter(), "winners": []}
    for ceremony, entries in best_picture_by_ceremony(competitive).items():
        for entry in entries:
            for item in entry["films"]:
                language["nominees"] += 1
                code = films[item["id"]].get("language")
                if code and code != "en":
                    language["nonEnglish"] += 1
                    language["byEra"][era_of(first_year(entry["year"]))] += 1
                    if entry["winner"]:
                        language["winners"].append({**film_summary(films[item["id"]]), "language": code, "ceremony": ceremony})
    language["byEra"] = [{"era": era, "nonEnglish": language["byEra"][era]} for era, _, _ in ERAS]

    return {
        "ages": {"actor": age_group(LEAD_ACTOR), "actress": age_group(LEAD_ACTRESS)},
        "eraGaps": era_gaps(),
        "crafts": crafts,
        "eras": [era for era, _, _ in ERAS],
        "directingWomen": {
            "nominations": len(directing_women),
            "winners": [row for row in directing_women if row["won"]],
            "first": min(directing_women, key=lambda row: row["ceremony"]) if directing_women else None,
        },
        "language": language,
    }


def build_snubbed(nominations, films, people, career_ids=CAREERS):
    competitive = competitive_only(nominations)
    careers = []
    for person_id in career_ids:
        tally = Counter()
        wins = Counter()
        for nomination in competitive:
            if any(nominee["id"] == person_id for nominee in nomination["nominees"]):
                tally[nomination["ceremony"]] += 1
                wins[nomination["ceremony"]] += nomination["winner"]
        points = []
        total = 0
        for ceremony in sorted(tally):
            total += tally[ceremony]
            points.append({"ceremony": ceremony, "nominations": total, "wins": wins[ceremony]})
        careers.append({"id": person_id, "name": people[person_id]["name"], "nominations": people[person_id]["nominations"], "wins": people[person_id]["wins"], "points": points})

    def top_empty(items, label):
        empty = [item for item in items if item["wins"] == 0 and item["nominations"] > 0]
        return sorted(empty, key=lambda item: (-item["nominations"], item[label]))[:LEADERBOARD_SIZE]

    return {
        "careers": careers,
        "films": [{**film_summary(film), "nominations": film["nominations"]} for film in top_empty(films.values(), "title")],
        "people": [
            {"id": person["id"], "name": person["name"], "nominations": person["nominations"], "honors": person["honors"]}
            for person in top_empty([person for person in people.values() if person["type"] == "person"], "name")
        ],
    }


def build_encore(nominations, films):
    """The big winners of each film year, for the birth-year lookup."""
    by_ceremony = defaultdict(lambda: {"year": "", "picture": None, "director": [], "actor": [], "actress": []})
    for nomination in competitive_only(nominations):
        entry = by_ceremony[nomination["ceremony"]]
        entry["year"] = nomination["year"]
        if not nomination["winner"]:
            continue
        names = [nominee["name"] for nominee in nomination["nominees"]]
        if nomination["category"] == BEST_PICTURE:
            entry["picture"] = film_summary(films[nomination["films"][0]["id"]])
        elif nomination["category"] in DIRECTING:
            entry["director"].extend(names)
        elif nomination["category"] == LEAD_ACTOR:
            entry["actor"].extend(names)
        elif nomination["category"] == LEAD_ACTRESS:
            entry["actress"].extend(names)
    return [{"ceremony": ceremony, **entry} for ceremony, entry in sorted(by_ceremony.items())]


def build_sweep(films):
    """A nominations-by-wins grid, plus every film named in the story copy."""
    nominated = [film for film in films if film["nominations"] > 0]
    cells = defaultdict(list)
    for film in nominated:
        cells[(film["nominations"], film["wins"])].append(film)

    def rank(film):
        return (-film["firstCeremony"], film["title"])

    grid = [
        {
            "nominations": nominations,
            "wins": wins,
            "count": len(members),
            "films": [film_summary(film) for film in sorted(members, key=rank)[:MAX_FILMS_PER_CELL]],
        }
        for (nominations, wins), members in sorted(cells.items())
    ]

    empty_handed = [film for film in nominated if film["wins"] == 0]
    perfect = [film for film in nominated if film["wins"] == film["nominations"] and film["wins"] >= 5]
    return {
        "totals": {
            "films": len(nominated),
            "emptyHanded": len(empty_handed),
            "emptyHandedShare": round(len(empty_handed) / len(nominated), 3),
            "maxNominations": max(film["nominations"] for film in nominated),
            "maxWins": max(film["wins"] for film in nominated),
        },
        "grid": grid,
        "perfect": [
            {**film_summary(film), "wins": film["wins"]}
            for film in sorted(perfect, key=lambda film: (-film["wins"], film["firstCeremony"]))
        ],
    }


def run():
    data = read_json(NORMALIZED_FILE)
    story = OUT / "story"
    nominations = data["nominations"]
    write_json(story / "meta.json", build_meta(data["ceremonies"]))
    write_json(story / "sweep.json", build_sweep(data["films"]))
    write_json(story / "overture.json", build_overture(nominations, data["ceremonies"]))
    write_json(story / "programme.json", build_programme(data["categories"], nominations, data["ceremonies"]))
    if not data.get("enriched"):
        print("  not enriched: skipping the acts that need film and person data")
        return
    films = {film["id"]: film for film in data["films"]}
    people = {person["id"]: person for person in data["people"]}
    write_json(story / "formula.json", build_formula(nominations, films))
    write_json(story / "money.json", build_money(nominations, films, load_cpi()))
    write_json(story / "audience.json", build_audience(nominations, films))
    write_json(story / "gold.json", build_gold(nominations, films, people))
    write_json(story / "snubbed.json", build_snubbed(nominations, films, people))
    write_json(story / "encore.json", build_encore(nominations, films))


if __name__ == "__main__":
    run()
