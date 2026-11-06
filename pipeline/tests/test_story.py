import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import story  # noqa: E402


def nomination(category, ceremony, year, winner=False, films=(), nominees=(), family="Picture", competitive=True):
    return {
        "category": category,
        "ceremony": ceremony,
        "year": year,
        "winner": winner,
        "competitive": competitive,
        "family": family,
        "films": [{"id": film_id, "title": film_id} for film_id in films],
        "nominees": [{"id": nominee_id, "name": nominee_id, "type": "person"} for nominee_id in nominees],
    }


def film(film_id, year="2000", **values):
    return {"id": film_id, "title": film_id, "filmYear": year, "poster": None, "firstCeremony": 73, "nominations": 1, "wins": 0, "private": {"imdbRating": 9.9}, **values}


class Helpers(unittest.TestCase):
    def test_split_year_uses_its_first_year(self):
        self.assertEqual(story.first_year("1927/28"), 1927)

    def test_every_film_year_has_an_era(self):
        self.assertEqual(story.era_of(1927), "1927-49")
        self.assertEqual(story.era_of(2025), "2010-25")
        with self.assertRaises(ValueError):
            story.era_of(1900)

    def test_share_of_nothing_is_none(self):
        self.assertIsNone(story.share(0, 0))


class Overture(unittest.TestCase):
    def test_honors_are_left_out(self):
        rows = [
            nomination("BEST PICTURE", 1, "2000", winner=True),
            nomination("BEST PICTURE", 1, "2000"),
            nomination("HONORARY AWARD", 1, "2000", winner=True, competitive=False),
        ]
        result = story.build_overture(rows, [{"ceremony": 1, "filmYear": "2000"}])
        self.assertEqual(result["totals"], {"nominations": 2, "wins": 1})


class Programme(unittest.TestCase):
    def test_counts_distinct_categories_per_family_and_night(self):
        rows = [
            nomination("ART DIRECTION (Color)", 1, "2000", family="Design"),
            nomination("ART DIRECTION (Color)", 1, "2000", family="Design"),
            nomination("COSTUME DESIGN", 1, "2000", family="Design"),
        ]
        categories = [
            {"name": "ART DIRECTION (Color)", "competitive": True, "lastCeremony": 1},
            {"name": "COSTUME DESIGN", "competitive": True, "lastCeremony": 2},
        ]
        ceremonies = [{"ceremony": 1, "filmYear": "2000", "competitiveCategories": 2}, {"ceremony": 2, "filmYear": "2001", "competitiveCategories": 1}]
        result = story.build_programme(categories, rows, ceremonies)
        design = next(family for family in result["families"] if family["name"] == "Design")
        self.assertEqual(design["counts"], [2, 0])
        self.assertEqual(result["facts"]["retired"], 1)
        self.assertEqual(result["facts"]["peak"], 2)


class Formula(unittest.TestCase):
    def rows(self):
        return [
            nomination("BEST PICTURE", 1, "2000", winner=True, films=["a"]),
            nomination("BEST PICTURE", 1, "2000", films=["b"]),
            nomination("DIRECTING", 1, "2000", winner=True, films=["a"]),
            nomination("FILM EDITING", 1, "2000", films=["b"]),
            nomination("CINEMATOGRAPHY", 1, "2000", films=["b"]),
        ]

    def test_flags_come_from_the_winner_only(self):
        result = story.build_formula(self.rows(), {"a": film("a"), "b": film("b")})
        winner = result["winners"][0]
        self.assertTrue(winner["directing"])
        self.assertFalse(winner["editing"])

    def test_most_nominated_compares_within_the_night(self):
        result = story.build_formula(self.rows(), {"a": film("a"), "b": film("b")})
        self.assertFalse(result["winners"][0]["mostNominated"])

    def test_tied_most_nominated_counts_as_leading(self):
        rows = self.rows()[:3] + [nomination("FILM EDITING", 1, "2000", films=["b"])]
        result = story.build_formula(rows, {"a": film("a"), "b": film("b")})
        self.assertTrue(result["winners"][0]["mostNominated"])

    def test_a_lone_entrant_has_no_field_to_lead(self):
        rows = [nomination("BEST PICTURE", 1, "2000", winner=True, films=["a"])]
        result = story.build_formula(rows, {"a": film("a")})
        self.assertFalse(result["winners"][0]["mostNominated"])
        era = next(row for row in result["eras"] if row["era"] == "1990-2009")
        self.assertIsNone(era["mostNominated"])
        self.assertEqual(era["directing"], 0.0)

    def test_era_shares(self):
        result = story.build_formula(self.rows(), {"a": film("a"), "b": film("b")})
        era = next(row for row in result["eras"] if row["era"] == "1990-2009")
        self.assertEqual((era["winners"], era["directing"], era["editing"]), (1, 1.0, 0.0))


class Money(unittest.TestCase):
    cpi = {2015: 100.0, 2025: 200.0}

    def test_revenue_is_adjusted_and_the_median_uses_winners_only(self):
        rows = [nomination("BEST PICTURE", 88, "2015", winner=True, films=["a"]), nomination("BEST PICTURE", 88, "2015", films=["b"])]
        result = story.build_money(rows, {"a": film("a", revenue=10), "b": film("b", revenue=50)}, self.cpi)
        decade = result["decades"][0]
        self.assertEqual((decade["decade"], decade["medianWinner"], decade["winnersKnown"], decade["nomineesKnown"]), (2010, 20, 1, 2))
        self.assertEqual(result["topGrosser"]["2010s"], {"won": 0, "ceremonies": 1})

    def test_a_lone_entrant_has_no_top_grosser_contest(self):
        rows = [nomination("BEST PICTURE", 88, "2015", winner=True, films=["a"])]
        result = story.build_money(rows, {"a": film("a", revenue=10)}, self.cpi)
        self.assertEqual(result["topGrosser"]["2010s"]["ceremonies"], 0)

    def test_a_night_with_unknown_revenue_is_not_compared(self):
        rows = [nomination("BEST PICTURE", 88, "2015", winner=True, films=["a"]), nomination("BEST PICTURE", 88, "2015", films=["b"])]
        result = story.build_money(rows, {"a": film("a", revenue=10), "b": film("b", revenue=None)}, self.cpi)
        self.assertEqual(result["topGrosser"]["2010s"]["ceremonies"], 0)
        self.assertEqual(len(result["nominees"]), 1)


class Audience(unittest.TestCase):
    def rows(self):
        return [nomination("BEST PICTURE", 1, "2000", winner=True, films=["a"]), nomination("BEST PICTURE", 1, "2000", films=["b"])]

    def test_winner_rank_and_gap(self):
        result = story.build_audience(self.rows(), {"a": film("a", rating=7.0, votes=100), "b": film("b", rating=8.0, votes=100)})
        night = result["nights"][0]
        self.assertEqual((night["rank"], night["gap"], night["favourite"]["id"]), (2, 1.0, "b"))
        self.assertEqual(result["chance"], 0.5)

    def test_tie_at_the_top_counts_as_rank_one(self):
        result = story.build_audience(self.rows(), {"a": film("a", rating=8.0, votes=100), "b": film("b", rating=8.0, votes=100)})
        self.assertEqual(result["nights"][0]["rank"], 1)

    def test_a_lone_entrant_is_not_a_contest(self):
        result = story.build_audience(self.rows()[:1], {"a": film("a", rating=7.0, votes=100)})
        self.assertEqual(result["ceremoniesCompared"], 0)

    def test_a_thinly_voted_nominee_drops_the_night(self):
        result = story.build_audience(self.rows(), {"a": film("a", rating=8.0, votes=100), "b": film("b", rating=9.0, votes=3)})
        self.assertEqual(result["ceremoniesCompared"], 0)

    def test_no_private_score_is_published(self):
        result = story.build_audience(self.rows(), {"a": film("a", rating=7.0, votes=100), "b": film("b", rating=8.0, votes=100)})
        self.assertNotIn("imdbRating", str(result))


class Gold(unittest.TestCase):
    def build(self, rows, people):
        films = {"a": film("a", language="ko"), "b": film("b", language="en")}
        return story.build_gold(rows, films, people)

    def test_age_is_film_year_minus_birth_year(self):
        rows = [
            nomination(story.LEAD_ACTOR, 1, "2000", winner=True, films=["b"], nominees=["m"]),
            nomination(story.LEAD_ACTRESS, 1, "2000", winner=True, films=["b"], nominees=["w"]),
        ]
        people = {"m": {"birthYear": 1950, "gender": "man"}, "w": {"birthYear": 1970, "gender": "woman"}}
        result = self.build(rows, people)
        self.assertEqual(result["ages"]["actor"]["median"], 50)
        self.assertEqual(result["ages"]["actress"]["median"], 30)

    def test_unknown_gender_stays_out_of_the_share(self):
        rows = [
            nomination(story.LEAD_ACTOR, 1, "2000", winner=True, films=["b"], nominees=["m"]),
            nomination(story.LEAD_ACTRESS, 1, "2000", winner=True, films=["b"], nominees=["w"]),
            nomination("DIRECTING", 1, "2000", nominees=["w", "x"], films=["b"]),
        ]
        people = {"m": {"birthYear": 1950, "gender": "man"}, "w": {"birthYear": 1970, "gender": "woman"}, "x": {"birthYear": 1970, "gender": None}}
        result = self.build(rows, people)
        directing = next(row for row in result["crafts"] if row["craft"] == "Directing")
        era = next(row for row in directing["eras"] if row["era"] == "1990-2009")
        self.assertEqual((era["women"], era["known"], era["share"]), (1, 1, 1.0))
        self.assertEqual(result["directingWomen"]["first"]["name"], "w")

    def test_language_counts_non_english_winners(self):
        rows = [
            nomination(story.LEAD_ACTOR, 1, "2000", winner=True, films=["b"], nominees=["m"]),
            nomination(story.LEAD_ACTRESS, 1, "2000", winner=True, films=["b"], nominees=["w"]),
            nomination("BEST PICTURE", 1, "2000", winner=True, films=["a"]),
            nomination("BEST PICTURE", 1, "2000", films=["b"]),
        ]
        people = {"m": {"birthYear": 1950, "gender": "man"}, "w": {"birthYear": 1970, "gender": "woman"}}
        language = self.build(rows, people)["language"]
        self.assertEqual((language["nominees"], language["nonEnglish"], language["winners"][0]["id"]), (2, 1, "a"))


class Snubbed(unittest.TestCase):
    def test_career_points_accumulate_and_honors_are_excluded(self):
        rows = [
            nomination("X", 1, "2000", nominees=["p"]),
            nomination("X", 3, "2002", winner=True, nominees=["p"]),
            nomination("HONORARY", 4, "2003", winner=True, nominees=["p"], competitive=False),
        ]
        people = {"p": {"id": "p", "type": "person", "name": "P", "nominations": 2, "wins": 1, "honors": 1}}
        career = story.build_snubbed(rows, {}, people, ["p"])["careers"][0]
        self.assertEqual([(point["ceremony"], point["nominations"], point["wins"]) for point in career["points"]], [(1, 1, 0), (3, 2, 1)])

    def test_leaderboards_hold_only_people_without_wins(self):
        people = {
            "a": {"id": "a", "type": "person", "name": "A", "nominations": 9, "wins": 1, "honors": 0},
            "b": {"id": "b", "type": "person", "name": "B", "nominations": 5, "wins": 0, "honors": 1},
            "c": {"id": "c", "type": "company", "name": "C", "nominations": 50, "wins": 0, "honors": 0},
        }
        result = story.build_snubbed([], {}, people, [])
        self.assertEqual(result["people"], [{"id": "b", "name": "B", "nominations": 5, "honors": 1}])


class Encore(unittest.TestCase):
    def test_tied_winners_are_both_kept(self):
        rows = [
            nomination(story.LEAD_ACTRESS, 41, "1968", winner=True, nominees=["Hepburn"]),
            nomination(story.LEAD_ACTRESS, 41, "1968", winner=True, nominees=["Streisand"]),
            nomination("BEST PICTURE", 41, "1968", winner=True, films=["a"]),
        ]
        entry = story.build_encore(rows, {"a": film("a", "1968")})[0]
        self.assertEqual(entry["actress"], ["Hepburn", "Streisand"])
        self.assertEqual(entry["picture"]["id"], "a")


if __name__ == "__main__":
    unittest.main()
