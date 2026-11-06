"""Read precursor award winners from Wikipedia's award pages and match them to Oscar nominees.

Writes data/precursors/wins.csv, the only precursor file the model reads, plus a per-award audit in
data/reports/precursors.md. Pages are cached in data/cache/precursors. Uses curl for the same certificate
reason as fetch_wikidata.py. Winners who weren't Oscar nominees are recorded too, because a parse that
found nothing and a winner the Academy skipped must not look the same.
"""
import csv
import re
import subprocess
import time
import unicodedata
import urllib.parse
from collections import defaultdict

from common import CACHE, DATA, NORMALIZED_FILE, REPORTS, USER_AGENT, read_json

WINS_FILE = DATA / "precursors" / "wins.csv"
PAGE_CACHE = CACHE / "precursors"
FIRST_YEAR = 1995
LAST_YEAR = 2025
PAUSE_SECONDS = 1.2
# A page may label a row by the film's year or by the ceremony's, usually the year after.
LABEL_OFFSETS = (0, 1)

# Award key: (Wikipedia page, Oscar category it predicts).
PAGES = {
    "dga": ("Directors Guild of America Award for Outstanding Directing – Feature Film", "DIRECTING"),
    "pga": ("Producers Guild of America Award for Best Theatrical Motion Picture", "BEST PICTURE"),
    "sag_cast": ("Screen Actors Guild Award for Outstanding Performance by a Cast in a Motion Picture", "BEST PICTURE"),
    "bafta_film": ("BAFTA Award for Best Film", "BEST PICTURE"),
    "gg_drama": ("Golden Globe Award for Best Motion Picture – Drama", "BEST PICTURE"),
    "gg_comedy": ("Golden Globe Award for Best Motion Picture – Musical or Comedy", "BEST PICTURE"),
    "cc_film": ("Critics' Choice Movie Award for Best Picture", "BEST PICTURE"),
    "bafta_director": ("BAFTA Award for Best Direction", "DIRECTING"),
    "gg_director": ("Golden Globe Award for Best Director", "DIRECTING"),
    "cc_director": ("Critics' Choice Movie Award for Best Director", "DIRECTING"),
    "sag_actor": ("Screen Actors Guild Award for Outstanding Performance by a Male Actor in a Leading Role", "ACTOR IN A LEADING ROLE"),
    "bafta_actor": ("BAFTA Award for Best Actor in a Leading Role", "ACTOR IN A LEADING ROLE"),
    "gg_actor_drama": ("Golden Globe Award for Best Actor – Motion Picture Drama", "ACTOR IN A LEADING ROLE"),
    "gg_actor_comedy": ("Golden Globe Award for Best Actor – Motion Picture Musical or Comedy", "ACTOR IN A LEADING ROLE"),
    "cc_actor": ("Critics' Choice Movie Award for Best Actor", "ACTOR IN A LEADING ROLE"),
    "sag_actress": ("Screen Actors Guild Award for Outstanding Performance by a Female Actor in a Leading Role", "ACTRESS IN A LEADING ROLE"),
    "bafta_actress": ("BAFTA Award for Best Actress in a Leading Role", "ACTRESS IN A LEADING ROLE"),
    "gg_actress_drama": ("Golden Globe Award for Best Actress in a Motion Picture – Drama", "ACTRESS IN A LEADING ROLE"),
    "gg_actress_comedy": ("Golden Globe Award for Best Actress in a Motion Picture – Comedy or Musical", "ACTRESS IN A LEADING ROLE"),
    "cc_actress": ("Critics' Choice Movie Award for Best Actress", "ACTRESS IN A LEADING ROLE"),
    "sag_supporting_actor": ("Screen Actors Guild Award for Outstanding Performance by a Male Actor in a Supporting Role", "ACTOR IN A SUPPORTING ROLE"),
    "bafta_supporting_actor": ("BAFTA Award for Best Actor in a Supporting Role", "ACTOR IN A SUPPORTING ROLE"),
    "gg_supporting_actor": ("Golden Globe Award for Best Supporting Actor – Motion Picture", "ACTOR IN A SUPPORTING ROLE"),
    "cc_supporting_actor": ("Critics' Choice Movie Award for Best Supporting Actor", "ACTOR IN A SUPPORTING ROLE"),
    "sag_supporting_actress": ("Screen Actors Guild Award for Outstanding Performance by a Female Actor in a Supporting Role", "ACTRESS IN A SUPPORTING ROLE"),
    "bafta_supporting_actress": ("BAFTA Award for Best Actress in a Supporting Role", "ACTRESS IN A SUPPORTING ROLE"),
    "gg_supporting_actress": ("Golden Globe Award for Best Supporting Actress – Motion Picture", "ACTRESS IN A SUPPORTING ROLE"),
    "cc_supporting_actress": ("Critics' Choice Movie Award for Best Supporting Actress", "ACTRESS IN A SUPPORTING ROLE"),
}

LINK = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
BOLD = re.compile(r"'''+(.+?)'''+")
CELL_ATTRIBUTE = re.compile(r"^\s*(?:[a-zA-Z-]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s|,]+)\s*,?\s*)+\|")
# A year cell is plain or exactly bold. Five quotes mean bold italics, which is how winning films are
# set, so the film 1917 isn't a year, and neither is 2001: A Space Odyssey.
YEAR_START = re.compile(r"^(?:''')?(19\d\d|20[0-2]\d)(?![:\d])\b(?!\s+[A-Z])")


def fold(text):
    """Lowercase, no accents, words separated by single spaces."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", ascii_text).split())


def plain(text):
    """Wikitext to readable text: links become their display text, and notes and tags go."""
    text = re.sub(r"<ref[^>]*/>|<ref.*?</ref>", "", text)
    text = re.sub(r"\{\{(?:sortname|sort)\|([^|}]*)\|([^|}]*)[^}]*\}\}", r"\1 \2", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return LINK.sub(r"\1", text)


def row_year(line):
    """The year a table row starts with, or None. Only a cell that opens with a year counts."""
    if not line.startswith(("|", "!")) or line.startswith(("|-", "|}", "|+")):
        return None
    cell = plain(line[1:])
    previous = None
    while cell != previous:
        previous = cell
        cell = CELL_ATTRIBUTE.sub("", cell)
    # Some pages wrap the year in a template, like {{center|'''1947'''...}}.
    cell = re.sub(r"^\s*\{\{[a-zA-Z]+\|", "", cell)
    match = YEAR_START.match(cell.strip())
    return int(match.group(1)) if match else None


def winners_by_year(wikitext):
    """For each labelled year, the bold text in that year's rows. Winners are bold on these pages."""
    found = defaultdict(list)
    year = None
    for line in wikitext.split("\n"):
        started = row_year(line)
        if started is not None:
            year = started
        if line.startswith(("=", "{|", "|}")) and started is None:
            if line.startswith("|}"):
                year = None
            continue
        if year is None:
            continue
        for span in BOLD.findall(line):
            text = plain(span).strip(" '\"")
            # The row's own bold year is structure. Any other number may be a title, like 1917.
            if text and text != str(year):
                found[year].append(text)
    return found


def contains_name(haystack, needle):
    """Whole-word match, so the film Up isn't found inside Up in the Air's row by accident."""
    return f" {needle} " in f" {haystack} "


def candidates_for(data, category, film_year):
    """Who could be matched: that category's nominees, by person name or film title."""
    rows = []
    for nomination in data["nominations"]:
        if nomination["category"] != category or not nomination["competitive"]:
            continue
        if int(nomination["year"].split("/")[0]) != film_year:
            continue
        rows.append(nomination)
    return rows


def same_person(span, name):
    """Handles Youn Yuh-jung for Yuh-Jung Youn, and Alejandro González Iñárritu for Alejandro G. Iñárritu."""
    span_words, name_words = fold(span).split(), fold(name).split()
    if sorted(span_words) == sorted(name_words):
        return True
    has_middle_name = len(span_words) >= 3 and len(name_words) >= 3
    return has_middle_name and span_words[0] == name_words[0] and span_words[-1] == name_words[-1]


def film_names(title):
    """A title and its short form: Birdman or (The Unexpected Virtue of Ignorance) is also just Birdman."""
    short = re.split(r"\s+or\s+\(|:\s", title, maxsplit=1)[0]
    # A short form of one word would match too easily, unless the title has a bracketed subtitle.
    keep_short = short != title and (" or (" in title or len(short.split()) >= 2)
    return [title, short] if keep_short else [title]


def match_winners(spans, nominees, by_film):
    """Ids of the nominees named in a year's bold text."""
    text = fold(" | ".join(spans))
    matched = {}
    for nomination in nominees:
        names = [film["title"] for film in nomination["films"]] if by_film else [person["name"] for person in nomination["nominees"]]
        ids = [film["id"] for film in nomination["films"]] if by_film else [person["id"] for person in nomination["nominees"]]
        for name, entity in zip(names, ids):
            if by_film:
                found = any(contains_name(text, fold(form)) for form in film_names(name))
            else:
                found = contains_name(text, fold(name)) or any(same_person(span, name) for span in spans)
            if found:
                # One person with two nominated films in a year still counts once.
                matched[entity] = name
    return list(matched.items())


def fetch_page(title):
    path = PAGE_CACHE / f"{fold(title).replace(' ', '_')}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    for _ in range(4):
        url = f"https://en.wikipedia.org/w/index.php?title={urllib.parse.quote(title.replace(' ', '_'))}&action=raw"
        result = subprocess.run(["curl", "-sSfL", "-m", "60", "-A", USER_AGENT, url], capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"Couldn't fetch {title}: {result.stderr.decode('utf-8', 'replace')[:160]}")
        text = result.stdout.decode("utf-8")
        redirect = re.match(r"#REDIRECT\s*\[\[([^\]#]+)", text, re.I)
        if not redirect:
            break
        title = redirect.group(1)
        time.sleep(PAUSE_SECONDS)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    time.sleep(PAUSE_SECONDS)
    return text


def extract_award(wikitext, data, category, by_film):
    """Tries each year-label convention and keeps whichever matches the most nominees."""
    found = winners_by_year(wikitext)
    best = None
    for offset in LABEL_OFFSETS:
        rows = {}
        for year in range(FIRST_YEAR, LAST_YEAR + 1):
            spans = found.get(year + offset, [])
            rows[year] = {"spans": spans, "matched": match_winners(spans, candidates_for(data, category, year), by_film)}
        score = sum(bool(row["matched"]) for row in rows.values())
        if best is None or score > best[0]:
            best = (score, offset, rows)
    return best[1], best[2]


def run():
    data = read_json(NORMALIZED_FILE)
    rows, audit = [], []
    for award, (page, category) in PAGES.items():
        by_film = category == "BEST PICTURE"
        offset, years = extract_award(fetch_page(page), data, category, by_film)
        # The Directors Guild honors a director, but Best Picture reads it through the film as well.
        film_years = extract_award(fetch_page(page), data, "BEST PICTURE", True)[1] if award == "dga" else {}
        matched_years = parsed_years = 0
        gaps = []
        for year, row in years.items():
            parsed_years += bool(row["spans"])
            matched_years += bool(row["matched"])
            if not row["spans"]:
                gaps.append(year)
            for entity, name in row["matched"]:
                rows.append({"award": award, "film_year": year, "id": entity, "name": name})
            for entity, name in film_years.get(year, {}).get("matched", []):
                rows.append({"award": award, "film_year": year, "id": entity, "name": name})
        audit.append((award, offset, parsed_years, matched_years, gaps))
        print(f"  {award:26} offset {offset}  years with a winner {parsed_years:2}  matched to a nominee {matched_years:2}  no winner found {gaps[:8]}", flush=True)

    WINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WINS_FILE, "w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=["award", "film_year", "id", "name"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: (row["award"], row["film_year"], row["id"])))

    lines = ["# Precursor audit", "", f"Film years {FIRST_YEAR} to {LAST_YEAR}. A year with a winner but no match means the winner wasn't an Oscar nominee in that category.", "", "| Award | Label offset | Years with a winner | Matched to a nominee | No winner found |", "|---|---:|---:|---:|---|"]
    lines += [f"| {award} | {offset} | {parsed} | {matched} | {', '.join(map(str, gaps)) or 'none'} |" for award, offset, parsed, matched, gaps in audit]
    (REPORTS / "precursors.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"  wrote {len(rows)} wins")


if __name__ == "__main__":
    run()
