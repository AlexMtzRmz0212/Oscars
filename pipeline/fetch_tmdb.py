"""Look up each film on TMDb by IMDb id. Resumable: finished films are kept in data/cache.

Needs TMDB_TOKEN in the environment or in .env.local. TMDb is free for non-commercial use with credit.
"""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from common import CACHE, ENRICH, NORMALIZED_FILE, ROOT, USER_AGENT, read_json, write_json

API = "https://api.themoviedb.org/3"
CACHE_FILE = CACHE / "tmdb.jsonl"
WORKERS = 8
MAX_ATTEMPTS = 5


def read_token():
    token = os.environ.get("TMDB_TOKEN")
    if token:
        return token
    env_file = ROOT / ".env.local"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("TMDB_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("TMDB_TOKEN is not set. Add it to .env.local (see .env.example).")


def get(path, token):
    """Returns parsed JSON, or None on 404. Backs off on rate limits and network errors."""
    request = urllib.request.Request(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": USER_AGENT},
    )
    for attempt in range(MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            if error.code == 401:
                raise SystemExit("TMDb rejected the token (401).") from None
            if error.code != 429 and error.code < 500:
                raise
        except (urllib.error.URLError, TimeoutError):
            pass
        if attempt == MAX_ATTEMPTS - 1:
            raise RuntimeError(f"TMDb request kept failing: {path}")
        time.sleep(2**attempt)


def positive(value):
    """TMDb uses 0 to mean unknown for money and runtime."""
    return value if value else None


def summarize_movie(movie):
    return {
        "kind": "movie",
        "tmdbId": movie["id"],
        "poster": movie.get("poster_path"),
        "language": movie.get("original_language"),
        "releaseDate": movie.get("release_date") or None,
        "budget": positive(movie.get("budget")),
        "revenue": positive(movie.get("revenue")),
        "runtime": positive(movie.get("runtime")),
        "rating": positive(movie.get("vote_average")),
        "votes": movie.get("vote_count") or 0,
        "genres": [genre["name"] for genre in movie.get("genres", [])],
        "countries": [country["iso_3166_1"] for country in movie.get("production_countries", [])],
        "companies": [company["name"] for company in movie.get("production_companies", [])],
    }


def is_stale(entry):
    """Movies saved before ratings were added get one more call, with the id already known."""
    return entry["kind"] == "movie" and "votes" not in entry


def lookup(imdb_id, token, known=None):
    if known and is_stale(known):
        movie = get(f"/movie/{known['tmdbId']}", token)
        if movie:
            return summarize_movie(movie)
    found = get(f"/find/{imdb_id}?external_source=imdb_id", token)
    movies = (found or {}).get("movie_results", [])
    if movies:
        movie = get(f"/movie/{movies[0]['id']}", token)
        if movie:
            return summarize_movie(movie)
    for kind, key in (("tv", "tv_results"), ("episode", "tv_episode_results")):
        results = (found or {}).get(key, [])
        if results:
            image = results[0].get("poster_path") or results[0].get("still_path")
            return {"kind": kind, "tmdbId": results[0]["id"], "poster": image, "language": results[0].get("original_language")}
    return {"kind": "missing"}


def load_cache():
    cache = {}
    if CACHE_FILE.exists():
        for line in CACHE_FILE.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            cache[entry["id"]] = entry["data"]
    return cache


def run():
    token = read_token()
    data = read_json(NORMALIZED_FILE)
    film_ids = sorted(film["id"] for film in data["films"] if film["id"].startswith("tt"))
    cache = load_cache()
    todo = [film_id for film_id in film_ids if film_id not in cache or is_stale(cache[film_id])]
    print(f"  {len(cache)} cached, {len(todo)} to fetch", flush=True)

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    done = [0]

    def work(film_id):
        result = lookup(film_id, token, cache.get(film_id))
        with lock:
            cache[film_id] = result
            handle.write(json.dumps({"id": film_id, "data": result}, ensure_ascii=False) + "\n")
            handle.flush()
            done[0] += 1
            if done[0] % 500 == 0:
                print(f"  {done[0]} of {len(todo)}", flush=True)

    with open(CACHE_FILE, "a", encoding="utf-8", newline="\n") as handle:
        with ThreadPoolExecutor(WORKERS) as pool:
            list(pool.map(work, todo))

    write_json(ENRICH / "tmdb.json", {film_id: cache[film_id] for film_id in film_ids})


if __name__ == "__main__":
    run()
