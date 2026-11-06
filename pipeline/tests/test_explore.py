import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import explore  # noqa: E402


def nomination(category, ceremony, winner=False, films=(), nominees=(), competitive=True, family="Picture", detail="", citation="", unofficial=False, note=""):
    return {
        "category": category,
        "ceremony": ceremony,
        "year": "2000",
        "winner": winner,
        "competitive": competitive,
        "inCompetitiveCategory": competitive,
        "unofficial": unofficial,
        "note": note,
        "family": family,
        "films": [{"id": film_id, "title": film_id} for film_id in films],
        "nominees": [{"id": person, "name": person.upper(), "type": "unknown" if person.startswith("unk-") else "person"} for person in nominees],
        "detail": detail,
        "citation": citation,
    }


def film(film_id, **values):
    return {"id": film_id, "title": film_id, "filmYear": "2000", "poster": None, "nominations": 1, "wins": 0, "honors": 0, "firstCeremony": 1, "private": {"imdbRating": 9.9}, **values}


def person(person_id, **values):
    return {"id": person_id, "name": person_id.upper(), "type": "person", "nominations": 1, "wins": 0, "honors": 0, "firstCeremony": 1, "lastCeremony": 1, "gender": "woman", "birthDate": "1950-02-03", "birthYear": 1950, **values}


class Labels(unittest.TestCase):
    def test_capitals_become_readable(self):
        self.assertEqual(explore.category_label("BEST PICTURE"), "Best Picture")
        self.assertEqual(explore.category_label("ACTOR IN A LEADING ROLE"), "Actor in a Leading Role")

    def test_bracket_text_is_left_alone(self):
        self.assertEqual(explore.category_label("WRITING (Adapted Screenplay)"), "Writing (Adapted Screenplay)")

    def test_shards_stay_in_range_and_are_stable(self):
        self.assertEqual(explore.shard_of("tt0120338"), sum(map(ord, "tt0120338")) % 100)
        self.assertLess(explore.shard_of("unk-some-name"), explore.SHARD_COUNT)


class Ceremonies(unittest.TestCase):
    def build(self):
        rows = [
            nomination("HONORARY AWARD", 1, winner=True, nominees=["h"], competitive=False, family="Honorary"),
            nomination("BEST PICTURE", 1, films=["b"]),
            nomination("BEST PICTURE", 1, winner=True, films=["a"]),
            nomination("DIRECTING", 1, films=["a"], family="Directing"),
        ]
        data = {"nominations": rows, "ceremonies": [{"ceremony": 1, "filmYear": "2000", "competitiveCategories": 2}]}
        return explore.build_ceremony_pages(data, {"a": film("a"), "b": film("b")})

    def test_programme_order_with_honors_last_and_winner_first(self):
        pages, index = self.build()
        categories = pages[1]["categories"]
        self.assertEqual([category["name"] for category in categories], ["Best Picture", "Directing", "Honorary Award"])
        self.assertEqual(categories[0]["entries"][0]["films"][0]["id"], "a")
        self.assertEqual(index[0]["bestPicture"]["id"], "a")


class Categories(unittest.TestCase):
    def test_leaders_skip_placeholders_and_rank_by_wins(self):
        rows = [
            nomination("X", 1, winner=True, nominees=["a"]),
            nomination("X", 2, nominees=["b"]),
            nomination("X", 3, nominees=["b"]),
            nomination("X", 3, winner=True, nominees=["unk-c"]),
        ]
        data = {"nominations": rows, "categories": [{"name": "X", "slug": "x", "family": "Picture", "competitive": True, "firstCeremony": 1, "lastCeremony": 3, "ceremonyCount": 3}]}
        pages, _ = explore.build_category_pages(data)
        self.assertEqual([leader["id"] for leader in pages["x"]["leaders"]], ["a", "b"])
        self.assertEqual([night["ceremony"] for night in pages["x"]["nights"]], [3, 2, 1])
        self.assertEqual(pages["x"]["nights"][0]["nominees"], 2)


class Privacy(unittest.TestCase):
    def data(self):
        return {
            "nominations": [nomination("X", 1, films=["a"], nominees=["p", "q"])],
            "films": [film("a"), film("b")],
            "people": [person("p"), person("q")],
            "categories": [],
            "ceremonies": [],
        }

    def test_film_pages_hold_no_private_fields(self):
        text = json.dumps(explore.build_film_shards(self.data()))
        self.assertNotIn("imdbRating", text)
        self.assertNotIn("private", text)

    def test_person_pages_hold_no_gender_or_full_birth_date(self):
        text = json.dumps(explore.build_people_shards(self.data()))
        self.assertNotIn("gender", text)
        self.assertNotIn("1950-02-03", text)
        self.assertIn("1950", text)


class People(unittest.TestCase):
    def test_partners_count_shared_nominations_and_skip_placeholders(self):
        data = {
            "nominations": [nomination("X", 1, nominees=["p", "q", "unk-r"]), nomination("Y", 2, nominees=["p", "q"])],
            "people": [person("p"), person("q"), person("unk-r", type="unknown")],
        }
        shard = explore.build_people_shards(data)[explore.shard_of("p")]["p"]
        self.assertEqual(shard["partners"], [{"id": "q", "name": "Q", "type": "person", "shared": 2}])


class Unofficial(unittest.TestCase):
    def test_note_is_kept_and_flagged_for_readers(self):
        view = explore.entry_view(nomination("X", 1, unofficial=True, note="came in 2nd|NOTE: THIS IS NOT AN OFFICIAL NOMINATION. Write-in."))
        self.assertTrue(view["unofficial"])
        self.assertEqual(view["note"], "came in 2nd Write-in.")

    def test_unofficial_rows_stay_out_of_leaders_and_counts(self):
        rows = [nomination("X", 1, winner=True, nominees=["a"]), nomination("X", 1, nominees=["b"], unofficial=True)]
        data = {"nominations": rows, "categories": [{"name": "X", "slug": "x", "family": "Picture", "competitive": True, "firstCeremony": 1, "lastCeremony": 1, "ceremonyCount": 1}]}
        page = explore.build_category_pages(data)[0]["x"]
        self.assertEqual([leader["id"] for leader in page["leaders"]], ["a"])
        self.assertEqual(page["nights"][0]["nominees"], 1)


class Ranks(unittest.TestCase):
    def test_ties_share_a_rank(self):
        rows = [nomination("X", 1, films=["a"]), nomination("Y", 1, films=["a"]), nomination("Z", 1, films=["b"]), nomination("W", 1, films=["c"])]
        data = {"nominations": rows, "films": [film("a"), film("b"), film("c")]}
        ranks = explore.film_ranks(data)
        self.assertEqual((ranks["a"]["rank"], ranks["b"]["rank"], ranks["c"]["rank"], ranks["a"]["of"]), (1, 2, 2, 3))


class Search(unittest.TestCase):
    def test_kinds_and_years(self):
        data = {
            "films": [film("a", filmYear="1927/28")],
            "people": [person("p"), person("c", type="company"), person("unk-u", type="unknown")],
            "categories": [{"name": "BEST PICTURE", "slug": "best-picture"}],
            "ceremonies": [{"ceremony": 1, "filmYear": "1927/28"}],
        }
        rows = explore.build_search(data)
        self.assertEqual([row["k"] for row in rows], ["film", "person", "studio", "person", "category", "ceremony"])
        self.assertEqual(rows[0]["y"], 1927)
        self.assertEqual(rows[4]["n"], "Best Picture")


if __name__ == "__main__":
    unittest.main()
