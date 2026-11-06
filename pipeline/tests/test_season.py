import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import season  # noqa: E402


def nomination(category, ceremony, year, film, winner=False, people=()):
    return {
        "category": category, "ceremony": ceremony, "year": str(year), "competitive": True, "winner": winner,
        "films": [{"id": film, "title": film.upper()}],
        "nominees": [{"id": person, "name": person.upper(), "type": "person"} for person in people],
    }


def history():
    rows = []
    for offset in range(12):
        ceremony, year = 80 + offset, 2007 + offset
        rows += [
            nomination("BEST PICTURE", ceremony, year, f"win{offset}", True),
            nomination("BEST PICTURE", ceremony, year, f"lose{offset}"),
            nomination("FILM EDITING", ceremony, year, f"win{offset}"),
        ]
    return {
        "nominations": rows,
        "categories": [{"name": "BEST PICTURE"}, {"name": "FILM EDITING"}, {"name": "DIRECTING"}],
    }


def ballot_row(category, film, ids="", names="", poster=""):
    return {"category": category, "film_id": film, "film_title": film.upper(), "nominee_ids": ids, "nominee_names": names, "poster": poster}


class Inputs(unittest.TestCase):
    def test_an_unknown_category_stops_the_build(self):
        with self.assertRaises(SystemExit):
            season.nominations_from([ballot_row("BEST VIBES", "a")], {"BEST PICTURE"})

    def test_ids_and_names_must_line_up(self):
        with self.assertRaises(SystemExit):
            season.nominations_from([ballot_row("DIRECTING", "a", "p|q", "P")], {"DIRECTING"})

    def test_an_unknown_award_stops_the_build(self):
        with self.assertRaises(SystemExit):
            season.season_wins([{"award": "gg_vibes", "id": "a", "name": "A"}])

    def test_a_winner_the_academy_skipped_still_counts_as_announced(self):
        wins, announced = season.season_wins([{"award": "pga", "id": "", "name": "Someone"}, {"award": "dga", "id": "a", "name": "A"}])
        self.assertEqual(announced, {"pga", "dga"})
        self.assertEqual(wins, {("dga", season.FILM_YEAR): {"a"}})


class Forecast(unittest.TestCase):
    def forecast(self, wins=None, announced=frozenset()):
        ballot = season.nominations_from([ballot_row("BEST PICTURE", "x"), ballot_row("BEST PICTURE", "y"), ballot_row("FILM EDITING", "x")], {"BEST PICTURE", "FILM EDITING"})
        return season.build_forecast(history(), {}, ballot, wins or {}, set(announced), {"x": "/x.jpg"})

    def test_a_contest_sums_to_one_and_sorts_by_probability(self):
        contest = self.forecast()[0]
        self.assertAlmostEqual(sum(nominee["probability"] for nominee in contest["nominees"]), 1, places=3)
        values = [nominee["probability"] for nominee in contest["nominees"]]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_the_model_learned_from_history_not_the_current_night(self):
        contest = self.forecast()[0]
        self.assertEqual(contest["nominees"][0]["films"], ["x"])
        self.assertGreater(contest["nominees"][0]["probability"], 0.5)

    def test_a_category_with_no_ballot_yet_is_left_out(self):
        self.assertEqual([contest["key"] for contest in self.forecast()], ["picture"])

    def test_posters_and_precursors_reach_the_page(self):
        wins = {("pga", season.FILM_YEAR): {"y"}}
        contest = self.forecast(wins, {"pga"})[0]
        y = next(nominee for nominee in contest["nominees"] if nominee["films"] == ["y"])
        x = next(nominee for nominee in contest["nominees"] if nominee["films"] == ["x"])
        self.assertEqual(y["precursors"], ["Producers Guild"])
        self.assertEqual(x["poster"], "/x.jpg")
        self.assertEqual((contest["awardsAnnounced"], contest["awardsTotal"]), (1, 7))


class Links(unittest.TestCase):
    def test_a_first_time_nominee_gets_no_link(self):
        nominee = {"films": ["new"], "people": ["newperson"]}
        contest = {"subject": "person"}
        self.assertIsNone(season.archive_link(nominee, contest, {"new"}, {"someone"}))
        self.assertIsNone(season.archive_link(nominee, {"subject": "film"}, {"other"}, {"newperson"}))

    def test_a_returning_nominee_links_to_their_own_page(self):
        nominee = {"films": ["f"], "people": ["p"]}
        self.assertEqual(season.archive_link(nominee, {"subject": "person"}, {"f"}, {"p"}), "/people/p")
        self.assertEqual(season.archive_link(nominee, {"subject": "film"}, {"f"}, {"p"}), "/films/f")


class Score(unittest.TestCase):
    forecast = [{"key": "picture", "label": "Best Picture", "nominees": [
        {"label": "A", "films": ["a"], "people": [], "probability": 0.7},
        {"label": "B", "films": ["b"], "people": [], "probability": 0.3},
    ]}]

    def test_a_right_pick(self):
        contests, tally = season.score(self.forecast, [{"category": "BEST PICTURE", "winner_id": "a"}])
        self.assertTrue(contests[0]["correct"])
        self.assertEqual(tally, {"hits": 1, "nights": 1})

    def test_a_wrong_pick(self):
        contests, tally = season.score(self.forecast, [{"category": "BEST PICTURE", "winner_id": "b"}])
        self.assertFalse(contests[0]["correct"])
        self.assertTrue(contests[0]["nominees"][1]["won"])
        self.assertEqual(tally, {"hits": 0, "nights": 1})

    def test_a_category_still_to_come_isnt_scored(self):
        contests, tally = season.score(self.forecast, [])
        self.assertIsNone(contests[0]["correct"])
        self.assertEqual(tally["nights"], 0)

    def test_a_winner_who_wasnt_nominated_stops_the_build(self):
        with self.assertRaises(SystemExit):
            season.score(self.forecast, [{"category": "BEST PICTURE", "winner_id": "zzz"}])


class Stages(unittest.TestCase):
    """The record's honesty depends on these."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        base = Path(self.folder.name)
        self.addCleanup(self.folder.cleanup)
        self.patches = [
            mock.patch.object(season, "NOMINEES_FILE", base / "nominees.csv"),
            mock.patch.object(season, "PRECURSORS_FILE", base / "precursors.csv"),
            mock.patch.object(season, "RESULTS_FILE", base / "results.csv"),
            mock.patch.object(season, "FROZEN_FILE", base / "frozen.json"),
        ]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.base = base

    def write_ballot(self):
        (self.base / "nominees.csv").write_text(
            "category,film_id,film_title,nominee_ids,nominee_names,poster\nBEST PICTURE,x,X,,,\nBEST PICTURE,y,Y,,,\nFILM EDITING,x,X,,,\n", encoding="utf-8"
        )

    def test_no_ballot_means_awaiting_nominations(self):
        self.assertEqual(season.build_page_data(history(), {})["stage"], "awaiting-nominations")

    def test_a_ballot_opens_the_forecast(self):
        self.write_ballot()
        page = season.build_page_data(history(), {})
        self.assertEqual(page["stage"], "open")
        self.assertEqual(page["contests"][0]["key"], "picture")

    def test_results_without_a_frozen_forecast_are_refused(self):
        self.write_ballot()
        (self.base / "results.csv").write_text("category,winner_id\nBEST PICTURE,x\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            season.build_page_data(history(), {})

    def test_a_frozen_forecast_ignores_later_changes(self):
        self.write_ballot()
        frozen = {"frozenAt": "2027-03-13T12:00:00+00:00", "contests": [{"key": "picture", "label": "Best Picture", "nominees": [{"label": "X", "films": ["x"], "people": [], "probability": 0.9}, {"label": "Y", "films": ["y"], "people": [], "probability": 0.1}]}]}
        (self.base / "frozen.json").write_text(json.dumps(frozen), encoding="utf-8")
        (self.base / "precursors.csv").write_text("award,id,name\npga,y,Y\n", encoding="utf-8")
        page = season.build_page_data(history(), {})
        self.assertEqual(page["stage"], "frozen")
        self.assertEqual(page["contests"][0]["nominees"][0]["probability"], 0.9)

    def test_results_score_the_frozen_forecast(self):
        frozen = {"frozenAt": "2027-03-13T12:00:00+00:00", "contests": [{"key": "picture", "label": "Best Picture", "nominees": [{"label": "X", "films": ["x"], "people": [], "probability": 0.9}, {"label": "Y", "films": ["y"], "people": [], "probability": 0.1}]}]}
        (self.base / "frozen.json").write_text(json.dumps(frozen), encoding="utf-8")
        (self.base / "results.csv").write_text("category,winner_id\nBEST PICTURE,y\n", encoding="utf-8")
        page = season.build_page_data(history(), {})
        self.assertEqual((page["stage"], page["score"]), ("scored", {"hits": 0, "nights": 1}))

    def test_freezing_twice_is_refused_and_leaves_the_first_alone(self):
        self.write_ballot()
        with mock.patch.object(season, "read_json", return_value=history()), mock.patch.object(season.predict, "load_wins", return_value={}):
            season.freeze()
            first = (self.base / "frozen.json").read_text(encoding="utf-8")
            with self.assertRaises(SystemExit):
                season.freeze()
        self.assertEqual((self.base / "frozen.json").read_text(encoding="utf-8"), first)

    def test_freezing_nothing_is_refused(self):
        with mock.patch.object(season, "read_json", return_value=history()), mock.patch.object(season.predict, "load_wins", return_value={}):
            with self.assertRaises(SystemExit):
                season.freeze()
        self.assertFalse((self.base / "frozen.json").exists())


if __name__ == "__main__":
    unittest.main()
