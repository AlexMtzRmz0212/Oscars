"""Forecast the six biggest categories, and test how the forecast would have done.

The model is a conditional logit: every nominee gets a score, and a night's scores become probabilities
that sum to 100%, because a category has one winner per night. Standard library only.

A nominee's features come from the ballot and from precursor awards, all known before the Oscars. Outcomes
at or after the night being predicted are never used. The backtest walks forward: each year is predicted
from earlier years only, so nothing from the future can reach a prediction.
"""
import csv
import math
from collections import Counter, defaultdict

from common import DATA, NORMALIZED_FILE, OUT, read_json, write_json

WINS_FILE = DATA / "precursors" / "wins.csv"
L2_PENALTY = 1.0
MAX_NEWTON_STEPS = 30
CONVERGED_AT = 1e-7
# Precursor records are complete from this film year, the first with every award but BAFTA.
FIRST_TRAINING_YEAR = 1995
# BAFTA moved ahead of the Oscars for films of 2000. Before that it came after, so it would leak the result.
FIRST_BAFTA_YEAR = 2000
MIN_TRAINING_NIGHTS = 10
CALIBRATION_BINS = 5

ACTING = {"ACTOR IN A LEADING ROLE", "ACTRESS IN A LEADING ROLE", "ACTOR IN A SUPPORTING ROLE", "ACTRESS IN A SUPPORTING ROLE"}
SCREENPLAY = {"WRITING (Adapted Screenplay)", "WRITING (Original Screenplay)"}

CONTESTS = {
    "picture": {"label": "Best Picture", "category": "BEST PICTURE", "subject": "film", "precursors": ["dga", "pga", "sag_cast", "bafta_film", "gg_drama", "gg_comedy", "cc_film"]},
    "director": {"label": "Best Director", "category": "DIRECTING", "subject": "person", "precursors": ["dga", "bafta_director", "gg_director", "cc_director"]},
    "actor": {"label": "Best Actor", "category": "ACTOR IN A LEADING ROLE", "subject": "person", "precursors": ["sag_actor", "bafta_actor", "gg_actor_drama", "gg_actor_comedy", "cc_actor"]},
    "actress": {"label": "Best Actress", "category": "ACTRESS IN A LEADING ROLE", "subject": "person", "precursors": ["sag_actress", "bafta_actress", "gg_actress_drama", "gg_actress_comedy", "cc_actress"]},
    "supporting_actor": {"label": "Best Supporting Actor", "category": "ACTOR IN A SUPPORTING ROLE", "subject": "person", "precursors": ["sag_supporting_actor", "bafta_supporting_actor", "gg_supporting_actor", "cc_supporting_actor"]},
    "supporting_actress": {"label": "Best Supporting Actress", "category": "ACTRESS IN A SUPPORTING ROLE", "subject": "person", "precursors": ["sag_supporting_actress", "bafta_supporting_actress", "gg_supporting_actress", "cc_supporting_actress"]},
}

BALLOT_FEATURES = {
    "nominations": "Film's total nominations",
    "picture_nominee": "Film also up for Best Picture",
    "directing_nominee": "Film also up for Directing",
    "editing_nominee": "Film also up for Film Editing",
    "screenplay_nominee": "Film also up for a screenplay",
    "acting_nominee": "Film also up for an acting award",
    "career_nominations": "Nominee's earlier nominations",
    "career_winner": "Nominee has won before",
}
PRECURSOR_LABELS = {
    "dga": "Directors Guild", "pga": "Producers Guild", "sag_cast": "SAG cast", "bafta_film": "BAFTA Best Film",
    "gg_drama": "Globe, Drama", "gg_comedy": "Globe, Comedy or Musical", "cc_film": "Critics Choice Best Picture",
    "bafta_director": "BAFTA Director", "gg_director": "Globe Director", "cc_director": "Critics Choice Director",
    "sag_actor": "SAG Actor", "bafta_actor": "BAFTA Actor", "gg_actor_drama": "Globe Actor, Drama", "gg_actor_comedy": "Globe Actor, Comedy or Musical", "cc_actor": "Critics Choice Actor",
    "sag_actress": "SAG Actress", "bafta_actress": "BAFTA Actress", "gg_actress_drama": "Globe Actress, Drama", "gg_actress_comedy": "Globe Actress, Comedy or Musical", "cc_actress": "Critics Choice Actress",
    "sag_supporting_actor": "SAG Supporting Actor", "bafta_supporting_actor": "BAFTA Supporting Actor", "gg_supporting_actor": "Globe Supporting Actor", "cc_supporting_actor": "Critics Choice Supporting Actor",
    "sag_supporting_actress": "SAG Supporting Actress", "bafta_supporting_actress": "BAFTA Supporting Actress", "gg_supporting_actress": "Globe Supporting Actress", "cc_supporting_actress": "Critics Choice Supporting Actress",
}


def film_year_of(year_text):
    return int(year_text.split("/")[0])


def feature_names(contest):
    names = ["nominations", "directing_nominee", "editing_nominee", "screenplay_nominee", "acting_nominee"]
    if contest["subject"] == "person":
        names = ["picture_nominee", *names, "career_nominations", "career_winner"]
    return [*names, *contest["precursors"]]


def ballot_profile(nominations):
    """What each film was up for each night, from the ballot alone. Never looks at who won."""
    counts = defaultdict(Counter)
    categories = defaultdict(lambda: defaultdict(set))
    for nomination in nominations:
        if not nomination["competitive"]:
            continue
        for film in nomination["films"]:
            counts[nomination["ceremony"]][film["id"]] += 1
            categories[nomination["ceremony"]][film["id"]].add(nomination["category"])
    return counts, categories


def career_history(nominations):
    """For each person, the nominations and wins they had before each ceremony."""
    history = defaultdict(list)
    for nomination in nominations:
        if nomination["competitive"]:
            for nominee in nomination["nominees"]:
                history[nominee["id"]].append((nomination["ceremony"], nomination["winner"]))
    return history


def career_before(history, person_ids, ceremony):
    earlier = [record for person in person_ids for record in history.get(person, []) if record[0] < ceremony]
    return len(earlier), any(won for _, won in earlier)


def precursor_active(award, film_year):
    return not award.startswith("bafta") or film_year >= FIRST_BAFTA_YEAR


def features_for(entry, contest, ceremony, film_year, counts, categories, history, wins):
    """One nominee's features. `wins` maps (award, film year) to the set of winning ids."""
    films = [film["id"] for film in entry["films"]]
    people = [nominee["id"] for nominee in entry["nominees"]]
    up_for = set().union(*(categories[ceremony].get(film, set()) for film in films)) if films else set()
    values = {
        # Scaled so one unit is a meaningful step, which keeps the penalty fair across features.
        "nominations": max((counts[ceremony].get(film, 0) for film in films), default=0) / 5,
        "picture_nominee": float("BEST PICTURE" in up_for),
        "directing_nominee": float("DIRECTING" in up_for),
        "editing_nominee": float("FILM EDITING" in up_for),
        "screenplay_nominee": float(bool(up_for & SCREENPLAY)),
        "acting_nominee": float(bool(up_for & ACTING)),
    }
    if contest["subject"] == "person":
        earlier, won_before = career_before(history, people, ceremony)
        values["career_nominations"] = math.log1p(earlier)
        values["career_winner"] = float(won_before)

    ids = films if contest["subject"] == "film" else people
    for award in contest["precursors"]:
        winners = wins.get((award, film_year), set())
        # The Directors Guild honors a person, so Best Picture reads it through the film as well.
        pool = {*ids, *people, *films} if award == "dga" else set(ids)
        values[award] = float(precursor_active(award, film_year) and bool(pool & winners))
    return [values[name] for name in feature_names(contest)]


def build_nights(data, wins, contest_key, first_year=FIRST_TRAINING_YEAR):
    """Every contested night of one category, oldest first."""
    contest = CONTESTS[contest_key]
    counts, categories = ballot_profile(data["nominations"])
    history = career_history(data["nominations"])

    entries = defaultdict(list)
    for nomination in data["nominations"]:
        if nomination["competitive"] and nomination["category"] == contest["category"]:
            entries[nomination["ceremony"]].append(nomination)

    nights = []
    for ceremony in sorted(entries):
        field = entries[ceremony]
        film_year = film_year_of(field[0]["year"])
        if film_year < first_year or len(field) < 2:
            continue
        nights.append({
            "ceremony": ceremony,
            "year": film_year,
            "nominees": [
                {
                    "label": label_of(entry, contest),
                    "films": [film["id"] for film in entry["films"]],
                    "people": [nominee["id"] for nominee in entry["nominees"]],
                    "nominations": counts[ceremony].get(entry["films"][0]["id"], 0) if entry["films"] else 0,
                    "features": features_for(entry, contest, ceremony, film_year, counts, categories, history, wins),
                    "won": entry["winner"],
                }
                for entry in field
            ],
        })
    return nights


def label_of(entry, contest):
    title = ", ".join(film["title"] for film in entry["films"])
    if contest["subject"] == "film":
        return title
    return f"{', '.join(nominee['name'] for nominee in entry['nominees'])} ({title})"


# --- The model ---


def softmax(scores):
    top = max(scores)
    powers = [math.exp(score - top) for score in scores]
    total = sum(powers)
    return [power / total for power in powers]


def score_night(weights, features):
    return softmax([sum(weight * value for weight, value in zip(weights, row)) for row in features])


def solve(matrix, vector):
    """Gaussian elimination with partial pivoting."""
    size = len(vector)
    rows = [row[:] + [value] for row, value in zip(matrix, vector)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(rows[row][column]))
        rows[column], rows[pivot] = rows[pivot], rows[column]
        lead = rows[column][column]
        for row in range(column + 1, size):
            factor = rows[row][column] / lead
            if factor:
                for index in range(column, size + 1):
                    rows[row][index] -= factor * rows[column][index]
    answer = [0.0] * size
    for column in range(size - 1, -1, -1):
        known = sum(rows[column][index] * answer[index] for index in range(column + 1, size))
        answer[column] = (rows[column][size] - known) / rows[column][column]
    return answer


def fit(nights, size, penalty=L2_PENALTY):
    """Newton's method on the penalized conditional log-likelihood, which has a single best answer."""
    weights = [0.0] * size
    for _ in range(MAX_NEWTON_STEPS):
        gradient = [-penalty * weight for weight in weights]
        hessian = [[penalty if row == column else 0.0 for column in range(size)] for row in range(size)]

        for night in nights:
            rows = [nominee["features"] for nominee in night["nominees"]]
            winners = [nominee["won"] for nominee in night["nominees"]]
            if not any(winners):
                continue
            share = 1 / sum(winners)
            probabilities = score_night(weights, rows)
            mean = [sum(p * row[index] for p, row in zip(probabilities, rows)) for index in range(size)]
            for row, won in zip(rows, winners):
                if won:
                    for index in range(size):
                        gradient[index] += share * (row[index] - mean[index])
            for a in range(size):
                for b in range(a, size):
                    value = sum(p * row[a] * row[b] for p, row in zip(probabilities, rows)) - mean[a] * mean[b]
                    hessian[a][b] += value
                    if a != b:
                        hessian[b][a] += value

        step = solve(hessian, gradient)
        weights = [weight + change for weight, change in zip(weights, step)]
        if max(abs(change) for change in step) < CONVERGED_AT:
            break
    return weights


# --- Rules the model has to beat ---


def most_nominated_rule(night):
    """The plan's baseline: back the film with the most nominations, splitting ties."""
    counts = [nominee["nominations"] for nominee in night["nominees"]]
    return split_among(counts)


def precursor_count_rule(night, contest):
    """A harder baseline anyone could run by hand: back whoever has won the most precursors, splitting ties."""
    names = feature_names(contest)
    indexes = [names.index(award) for award in contest["precursors"]]
    return split_among([sum(nominee["features"][index] for index in indexes) for nominee in night["nominees"]])


def split_among(values):
    top = max(values)
    leaders = sum(value == top for value in values)
    return [1 / leaders if value == top else 0.0 for value in values]


# --- Scoring ---


def score_probabilities(probabilities, winners):
    """Hit credit, splitting a tie at the top, and log loss with a floor so a flat rule stays finite."""
    top = max(probabilities)
    leaders = [index for index, value in enumerate(probabilities) if value == top]
    hit = sum(1 for index in leaders if winners[index]) / len(leaders)
    won = sum(probability for probability, winner in zip(probabilities, winners) if winner) / max(1, sum(winners))
    return hit, -math.log(max(won, 0.001))


def walk_forward(nights, contest, min_training=MIN_TRAINING_NIGHTS):
    """Predict each night from earlier nights only."""
    size = len(feature_names(contest))
    results = []
    for index in range(min_training, len(nights)):
        night = nights[index]
        weights = fit(nights[:index], size)
        rows = [nominee["features"] for nominee in night["nominees"]]
        winners = [nominee["won"] for nominee in night["nominees"]]
        results.append({
            "ceremony": night["ceremony"],
            "year": night["year"],
            "labels": [nominee["label"] for nominee in night["nominees"]],
            "winners": winners,
            "model": score_night(weights, rows),
            "mostNominated": most_nominated_rule(night),
            "precursorCount": precursor_count_rule(night, contest),
            "chance": [1 / len(rows)] * len(rows),
        })
    return results


def summarize(results, key):
    scores = [score_probabilities(result[key], result["winners"]) for result in results]
    count = len(scores)
    return {
        "hits": round(sum(hit for hit, _ in scores), 2),
        "nights": count,
        "hitRate": round(sum(hit for hit, _ in scores) / count, 3) if count else None,
        "logLoss": round(sum(loss for _, loss in scores) / count, 3) if count else None,
    }


def calibration(results, bins=CALIBRATION_BINS):
    """When the model said 30%, did it happen about 30% of the time?"""
    buckets = [[] for _ in range(bins)]
    for result in results:
        for probability, won in zip(result["model"], result["winners"]):
            buckets[min(int(probability * bins), bins - 1)].append((probability, won))
    return [
        {
            "from": index / bins,
            "to": (index + 1) / bins,
            "nominees": len(bucket),
            "predicted": round(sum(p for p, _ in bucket) / len(bucket), 3),
            "actual": round(sum(won for _, won in bucket) / len(bucket), 3),
        }
        for index, bucket in enumerate(buckets)
        if bucket
    ]


def night_view(result):
    order = sorted(range(len(result["labels"])), key=lambda index: -result["model"][index])
    pick = order[0]
    winner = next(index for index, won in enumerate(result["winners"]) if won)
    return {
        "ceremony": result["ceremony"],
        "year": result["year"],
        "pick": result["labels"][pick],
        "pickProbability": round(result["model"][pick], 3),
        "winner": result["labels"][winner],
        "winnerProbability": round(result["model"][winner], 3),
        "correct": bool(result["winners"][pick]),
    }


def weight_view(contest, weights):
    labels = {**BALLOT_FEATURES, **PRECURSOR_LABELS}
    rows = [{"feature": name, "label": labels[name], "weight": round(weight, 3)} for name, weight in zip(feature_names(contest), weights)]
    return sorted(rows, key=lambda row: -abs(row["weight"]))


def load_wins(path=WINS_FILE):
    wins = defaultdict(set)
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            wins[(row["award"], int(row["film_year"]))].add(row["id"])
    return dict(wins)


def build_backtest(data, wins):
    contests, everything = [], []
    for key, contest in CONTESTS.items():
        nights = build_nights(data, wins, key)
        results = walk_forward(nights, contest)
        everything.extend(results)
        weights = fit(nights, len(feature_names(contest)))
        contests.append({
            "key": key,
            "label": contest["label"],
            "model": summarize(results, "model"),
            "mostNominated": summarize(results, "mostNominated"),
            "precursorCount": summarize(results, "precursorCount"),
            "chance": summarize(results, "chance"),
            "nights": [night_view(result) for result in reversed(results)],
            "weights": weight_view(contest, weights),
        })
    return {
        "firstYear": min(result["year"] for result in everything),
        "lastYear": max(result["year"] for result in everything),
        "trainingStarts": FIRST_TRAINING_YEAR,
        "overall": {key: summarize(everything, key) for key in ("model", "mostNominated", "precursorCount", "chance")},
        "contests": contests,
        "calibration": calibration(everything),
    }


def run():
    data = read_json(NORMALIZED_FILE)
    if not WINS_FILE.exists():
        print("  no precursor file in data/precursors, skipping")
        return
    backtest = build_backtest(data, load_wins())
    write_json(OUT / "season" / "backtest.json", backtest)
    overall = backtest["overall"]
    print(f"  {backtest['firstYear']} to {backtest['lastYear']}: model {overall['model']['hitRate']}, most nominated {overall['mostNominated']['hitRate']}, most precursors {overall['precursorCount']['hitRate']}")


if __name__ == "__main__":
    run()
