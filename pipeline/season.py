"""The live forecast for the 99th ceremony, from three hand-kept files in data/season_99.

The awards dataset updates weeks after each ceremony, so this season has its own files. See the README
there for what to do on each date. Run `python season.py freeze` the day before the ceremony: a frozen
forecast can't be overwritten, and results can't be scored without one, so the record can't be flattered
after the fact.
"""
import csv
import json
import sys
from datetime import datetime, timezone

import predict
from common import DATA, NORMALIZED_FILE, OUT, read_json, write_json

SEASON_DIR = DATA / "season_99"
NOMINEES_FILE = SEASON_DIR / "nominees.csv"
PRECURSORS_FILE = SEASON_DIR / "precursors.csv"
RESULTS_FILE = SEASON_DIR / "results.csv"
FROZEN_FILE = SEASON_DIR / "frozen.json"

CEREMONY = 99
FILM_YEAR = 2026
# From the Academy's April 2026 announcement. It says these dates may change.
SCHEDULE = [
    {"label": "Shortlists announced", "date": "2026-12-15"},
    {"label": "Nominations announced", "date": "2027-01-21"},
    {"label": "This forecast freezes", "date": "2027-03-13"},
    {"label": "The 99th ceremony", "date": "2027-03-14"},
]
MULTI_SEPARATOR = "|"
AWARDS = {award for contest in predict.CONTESTS.values() for award in contest["precursors"]}


def read_rows(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle) if any((value or "").strip() for value in row.values())]


def nominations_from(rows, known_categories):
    """The season's ballot, shaped like the historical data so one code path serves both."""
    nominations = []
    for row in rows:
        category = row["category"].strip()
        if category not in known_categories:
            raise SystemExit(f"Unknown category in nominees.csv: {category!r}. Use the canonical name, such as BEST PICTURE.")
        ids = [value.strip() for value in row["nominee_ids"].split(MULTI_SEPARATOR) if value.strip()]
        names = [value.strip() for value in row["nominee_names"].split(MULTI_SEPARATOR) if value.strip()]
        if len(ids) != len(names):
            raise SystemExit(f"Nominee ids and names don't line up in nominees.csv: {row}")
        film_id, film_title = row["film_id"].strip(), row["film_title"].strip()
        nominations.append({
            "ceremony": CEREMONY,
            "year": str(FILM_YEAR),
            "category": category,
            "competitive": True,
            "winner": False,
            "films": [{"id": film_id, "title": film_title}] if film_id else [],
            "nominees": [{"id": person, "name": name, "type": "person"} for person, name in zip(ids, names)],
        })
    return nominations


def season_wins(rows):
    """Winners so far, and which awards have been announced. A winner the Academy skipped has no id."""
    wins, announced = {}, set()
    for row in rows:
        award = row["award"].strip()
        if award not in AWARDS:
            raise SystemExit(f"Unknown award in precursors.csv: {award!r}")
        announced.add(award)
        if row.get("id", "").strip():
            wins.setdefault((award, FILM_YEAR), set()).add(row["id"].strip())
    return wins, announced


def archive_link(nominee, contest, film_ids, person_ids):
    """A first-time nominee has no Archive page until the dataset catches up, so it gets no link."""
    if contest["subject"] == "person":
        return next((f"/people/{person}" for person in nominee["people"] if person in person_ids), None)
    return next((f"/films/{film}" for film in nominee["films"] if film in film_ids), None)


def build_forecast(data, history_wins, ballot, wins, announced, posters):
    combined = {"nominations": [*data["nominations"], *ballot]}
    film_ids = {film["id"] for film in data.get("films", [])}
    person_ids = {person["id"] for person in data.get("people", [])}
    all_wins = {**history_wins, **wins}
    contests = []
    for key, contest in predict.CONTESTS.items():
        nights = predict.build_nights(combined, all_wins, key)
        current = next((night for night in nights if night["ceremony"] == CEREMONY), None)
        if current is None:
            continue
        past = [night for night in nights if night["ceremony"] < CEREMONY]
        weights = predict.fit(past, len(predict.feature_names(contest)))
        rows = [nominee["features"] for nominee in current["nominees"]]
        names = predict.feature_names(contest)
        probabilities = predict.score_night(weights, rows)
        nominees = [
            {
                "label": nominee["label"],
                "films": nominee["films"],
                "people": nominee["people"],
                "poster": next((posters[film] for film in nominee["films"] if film in posters), None),
                "link": archive_link(nominee, contest, film_ids, person_ids),
                "probability": round(probability, 4),
                "precursors": [predict.PRECURSOR_LABELS[award] for award in contest["precursors"] if nominee["features"][names.index(award)]],
            }
            for nominee, probability in zip(current["nominees"], probabilities)
        ]
        contests.append({
            "key": key,
            "label": contest["label"],
            "awardsAnnounced": sum(award in announced for award in contest["precursors"]),
            "awardsTotal": len(contest["precursors"]),
            "nominees": sorted(nominees, key=lambda nominee: -nominee["probability"]),
        })
    return contests


def score(forecast, results):
    """Marks each winner against the frozen forecast."""
    winners = {row["category"].strip(): row["winner_id"].strip() for row in results}
    scored, hits, nights = [], 0, 0
    for contest in forecast:
        category = predict.CONTESTS[contest["key"]]["category"]
        winner = winners.get(category)
        nominees = [{**nominee, "won": bool(winner) and winner in {*nominee["films"], *nominee["people"]}} for nominee in contest["nominees"]]
        if winner and not any(nominee["won"] for nominee in nominees):
            raise SystemExit(f"results.csv names {winner} for {category}, who isn't among the nominees.")
        correct = None
        if winner:
            nights += 1
            correct = nominees[0]["won"]
            hits += correct
        scored.append({**contest, "nominees": nominees, "correct": correct})
    return scored, {"hits": hits, "nights": nights}


def build_page_data(data, history_wins):
    ballot_rows = read_rows(NOMINEES_FILE)
    results = read_rows(RESULTS_FILE)
    known = {category["name"] for category in data["categories"]}
    frozen = json.loads(FROZEN_FILE.read_text(encoding="utf-8")) if FROZEN_FILE.exists() else None

    if results and not frozen:
        raise SystemExit("results.csv has results but the forecast was never frozen, so there is nothing fair to score.")

    page = {"ceremony": CEREMONY, "filmYear": FILM_YEAR, "schedule": SCHEDULE, "frozenAt": None, "score": None}
    if frozen:
        contests, tally = score(frozen["contests"], results)
        page.update(stage="scored" if results else "frozen", frozenAt=frozen["frozenAt"], contests=contests, score=tally if results else None)
        return page

    if not ballot_rows:
        page.update(stage="awaiting-nominations", contests=[])
        return page

    wins, announced = season_wins(read_rows(PRECURSORS_FILE))
    posters = {row["film_id"].strip(): row["poster"].strip() for row in ballot_rows if row.get("poster", "").strip()}
    page.update(stage="open", contests=build_forecast(data, history_wins, nominations_from(ballot_rows, known), wins, announced, posters))
    return page


def freeze():
    if FROZEN_FILE.exists():
        raise SystemExit("The forecast is already frozen, and a frozen forecast is never overwritten.")
    data = read_json(NORMALIZED_FILE)
    page = build_page_data(data, predict.load_wins())
    if page["stage"] != "open":
        raise SystemExit("There is no forecast to freeze yet: nominees.csv is empty.")
    payload = {"frozenAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "contests": page["contests"]}
    FROZEN_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"  froze the forecast at {payload['frozenAt']}")


def run():
    if not predict.WINS_FILE.exists():
        print("  no precursor file in data/precursors, skipping")
        return
    page = build_page_data(read_json(NORMALIZED_FILE), predict.load_wins())
    write_json(OUT / "season" / "season.json", page)
    print(f"  stage: {page['stage']}")


if __name__ == "__main__":
    if sys.argv[1:] == ["freeze"]:
        freeze()
    else:
        run()
