"""Look up birth date, gender and birth country for each nominee on Wikidata, joined by IMDb id.

Uses curl rather than urllib: Python's certificate store on Windows can reject Wikidata's
valid Let's Encrypt chain, and curl verifies certificates against the system store.
Resumable: finished batches are kept in data/cache.
"""
import json
import re
import subprocess
import time
from collections import defaultdict

from common import CACHE, ENRICH, NORMALIZED_FILE, USER_AGENT, read_json, write_json

ENDPOINT = "https://query.wikidata.org/sparql"
CACHE_FILE = CACHE / "wikidata.jsonl"
BATCH_SIZE = 200
PAUSE_SECONDS = 1.5
MAX_ATTEMPTS = 5
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T")

QUERY = """
SELECT ?imdb ?birth ?genderLabel ?countryLabel WHERE {
  VALUES ?imdb { %s }
  ?person wdt:P345 ?imdb .
  OPTIONAL { ?person wdt:P569 ?birth }
  OPTIONAL { ?person wdt:P21 ?gender }
  OPTIONAL { ?person wdt:P19 ?place . ?place wdt:P17 ?country }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
"""


def run_query(ids):
    query = QUERY % " ".join(f'"{person_id}"' for person_id in ids)
    command = [
        "curl", "-sSfL", "-m", "120", "-A", USER_AGENT,
        "-H", "Accept: application/sparql-results+json",
        "--data-urlencode", f"query={query}",
        ENDPOINT,
    ]
    for attempt in range(MAX_ATTEMPTS):
        result = subprocess.run(command, capture_output=True)
        if result.returncode == 0:
            return json.loads(result.stdout.decode("utf-8"))["results"]["bindings"]
        if attempt == MAX_ATTEMPTS - 1:
            raise RuntimeError(f"Wikidata query kept failing: {result.stderr.decode('utf-8', 'replace')[:200]}")
        time.sleep(10 * (attempt + 1))


def summarize(bindings):
    """Collapse one row per value combination into one entry per person.

    A person can carry several values. A real date beats Wikidata's "unknown value" placeholder,
    and conflicting birth dates are kept so the coverage report can count them.
    """
    collected = defaultdict(lambda: {"births": set(), "genders": set(), "countries": set()})
    for row in bindings:
        entry = collected[row["imdb"]["value"]]
        birth = row.get("birth", {}).get("value", "")
        if DATE_PATTERN.match(birth):
            entry["births"].add(birth[:10])
        gender = row.get("genderLabel", {}).get("value", "")
        if gender and not gender.startswith(("Q", "t", "_:")):
            entry["genders"].add(gender)
        country = row.get("countryLabel", {}).get("value", "")
        if country and not re.fullmatch(r"Q\d+", country):
            entry["countries"].add(country)

    return {
        person_id: {
            "birthDates": sorted(entry["births"]),
            "genders": sorted(entry["genders"]),
            "countries": sorted(entry["countries"]),
        }
        for person_id, entry in collected.items()
    }


def run():
    data = read_json(NORMALIZED_FILE)
    person_ids = sorted(person["id"] for person in data["people"] if person["id"].startswith("nm"))

    finished, results = set(), {}
    if CACHE_FILE.exists():
        for line in CACHE_FILE.read_text(encoding="utf-8").splitlines():
            batch = json.loads(line)
            finished.update(batch["ids"])
            results.update(batch["people"])

    todo = [person_id for person_id in person_ids if person_id not in finished]
    print(f"  {len(finished)} cached, {len(todo)} to fetch", flush=True)

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "a", encoding="utf-8", newline="\n") as handle:
        for start in range(0, len(todo), BATCH_SIZE):
            ids = todo[start : start + BATCH_SIZE]
            people = summarize(run_query(ids))
            results.update(people)
            handle.write(json.dumps({"ids": ids, "people": people}, ensure_ascii=False) + "\n")
            handle.flush()
            print(f"  {start + len(ids)} of {len(todo)}", flush=True)
            time.sleep(PAUSE_SECONDS)

    write_json(ENRICH / "wikidata.json", {person_id: results[person_id] for person_id in person_ids if person_id in results})
    print(f"  matched {len(results)} of {len(person_ids)} people")


if __name__ == "__main__":
    run()
