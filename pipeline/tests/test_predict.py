import copy
import math
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import predict  # noqa: E402

PICTURE = predict.CONTESTS["picture"]
ACTOR = predict.CONTESTS["actor"]


def nomination(category, ceremony, year, film, winner=False, people=(), competitive=True):
    return {
        "category": category,
        "ceremony": ceremony,
        "year": str(year),
        "competitive": competitive,
        "winner": winner,
        "films": [{"id": film, "title": film.upper()}],
        "nominees": [{"id": person, "name": person.upper(), "type": "person"} for person in people],
    }


def season(ceremony, year, winner="a"):
    """One small ballot where film a leads."""
    return [
        nomination("BEST PICTURE", ceremony, year, "a", winner == "a"),
        nomination("BEST PICTURE", ceremony, year, "b", winner == "b"),
        nomination("DIRECTING", ceremony, year, "a", True, ["d"]),
        nomination("FILM EDITING", ceremony, year, "a"),
    ]


def data_from(*seasons):
    return {"nominations": [row for rows in seasons for row in rows]}


class Softmax(unittest.TestCase):
    def test_a_night_sums_to_one(self):
        self.assertAlmostEqual(sum(predict.score_night([1.0, -2.0], [[1, 0], [0, 1], [1, 1]])), 1.0)

    def test_huge_scores_stay_finite(self):
        result = predict.softmax([1000.0, 0.0])
        self.assertAlmostEqual(result[0], 1.0)
        self.assertFalse(any(math.isnan(value) for value in result))


class Solver(unittest.TestCase):
    def test_solves_a_known_system(self):
        answer = predict.solve([[2.0, 1.0], [1.0, 3.0]], [3.0, 5.0])
        self.assertAlmostEqual(answer[0], 0.8)
        self.assertAlmostEqual(answer[1], 1.4)

    def test_pivots_past_a_zero(self):
        answer = predict.solve([[0.0, 1.0], [1.0, 0.0]], [2.0, 3.0])
        self.assertEqual(answer, [3.0, 2.0])


class Fit(unittest.TestCase):
    def nights(self, count=30, seed=4):
        """Feature 0 predicts the winner 80% of the time, and feature 1 is noise."""
        random_source = random.Random(seed)
        nights = []
        for _ in range(count):
            winner = 0 if random_source.random() < 0.8 else 1
            nights.append({"nominees": [
                {"features": [1.0, random_source.random()], "won": winner == 0},
                {"features": [0.0, random_source.random()], "won": winner == 1},
            ]})
        return nights

    def test_recovers_the_true_weight_and_ignores_the_noise(self):
        """An 80% signal has log odds of ln(4), about 1.39."""
        weights = predict.fit(self.nights(count=300), 2)
        self.assertAlmostEqual(weights[0], math.log(4), delta=0.3)
        self.assertLess(abs(weights[1]), 0.4)

    def test_penalty_shrinks_weights(self):
        loose = predict.fit(self.nights(), 2, penalty=0.1)
        tight = predict.fit(self.nights(), 2, penalty=50.0)
        self.assertLess(abs(tight[0]), abs(loose[0]))

    def test_a_dead_feature_gets_no_weight(self):
        nights = [{"nominees": [{"features": [1.0], "won": True}, {"features": [1.0], "won": False}]}] * 6
        self.assertAlmostEqual(predict.fit(nights, 1)[0], 0.0)


class Rules(unittest.TestCase):
    def test_ties_split_the_credit(self):
        self.assertEqual(predict.split_among([3, 3, 1, 0]), [0.5, 0.5, 0.0, 0.0])

    def test_a_tied_pick_earns_part_of_a_hit(self):
        hit, _ = predict.score_probabilities([0.5, 0.5, 0.0], [True, False, False])
        self.assertEqual(hit, 0.5)

    def test_zero_probability_on_the_winner_stays_finite(self):
        _, loss = predict.score_probabilities([1.0, 0.0], [False, True])
        self.assertTrue(math.isfinite(loss))


class NoLeakage(unittest.TestCase):
    """The promises the backtest's honesty rests on."""

    def history(self):
        rows = []
        for offset in range(16):
            rows.append(season(70 + offset, 1995 + offset, "a" if offset % 3 else "b"))
        return rows

    def wins(self):
        return {("pga", 1995 + offset): {"a" if offset % 2 else "b"} for offset in range(16)}

    def test_who_won_a_night_never_changes_that_nights_features(self):
        before = predict.build_nights(data_from(*self.history()), self.wins(), "picture")
        flipped = copy.deepcopy(self.history())
        for row in flipped[-1]:
            row["winner"] = not row["winner"]
        after = predict.build_nights(data_from(*flipped), self.wins(), "picture")
        self.assertEqual(
            [nominee["features"] for nominee in before[-1]["nominees"]],
            [nominee["features"] for nominee in after[-1]["nominees"]],
        )

    def test_a_later_result_never_changes_an_earlier_prediction(self):
        original = self.history()
        before = predict.walk_forward(predict.build_nights(data_from(*original), self.wins(), "picture"), PICTURE)
        changed = copy.deepcopy(original)
        for row in changed[-1]:
            row["winner"] = not row["winner"]
        after = predict.walk_forward(predict.build_nights(data_from(*changed), self.wins(), "picture"), PICTURE)
        self.assertEqual(before[0]["model"], after[0]["model"])
        self.assertEqual(before[-2]["model"], after[-2]["model"])

    def test_the_last_nights_own_result_doesnt_reach_its_prediction(self):
        original = self.history()
        before = predict.walk_forward(predict.build_nights(data_from(*original), self.wins(), "picture"), PICTURE)
        changed = copy.deepcopy(original)
        for row in changed[-1]:
            row["winner"] = not row["winner"]
        after = predict.walk_forward(predict.build_nights(data_from(*changed), self.wins(), "picture"), PICTURE)
        self.assertEqual(before[-1]["model"], after[-1]["model"])

    def test_career_counts_only_earlier_ceremonies(self):
        history = {"p": [(10, True), (20, False), (30, True)]}
        self.assertEqual(predict.career_before(history, ["p"], 20), (1, True))
        self.assertEqual(predict.career_before(history, ["p"], 10), (0, False))

    def test_a_later_win_doesnt_count_as_having_won_before(self):
        rows = [
            nomination("ACTOR IN A LEADING ROLE", 70, 1996, "a", False, ["p"]),
            nomination("ACTOR IN A LEADING ROLE", 70, 1996, "b", True, ["q"]),
            nomination("ACTOR IN A LEADING ROLE", 71, 1997, "c", True, ["p"]),
            nomination("ACTOR IN A LEADING ROLE", 71, 1997, "d", False, ["q"]),
        ]
        nights = predict.build_nights({"nominations": rows}, {}, "actor")
        names = predict.feature_names(ACTOR)
        first_p = nights[0]["nominees"][0]["features"]
        second_q = nights[1]["nominees"][1]["features"]
        self.assertEqual(first_p[names.index("career_winner")], 0.0)
        self.assertEqual(second_q[names.index("career_winner")], 1.0)

    def test_bafta_before_2000_is_ignored_because_it_came_after_the_oscars(self):
        rows = season(70, 1996) + season(75, 2001)
        wins = {("bafta_film", 1996): {"a"}, ("bafta_film", 2001): {"a"}}
        nights = predict.build_nights({"nominations": rows}, wins, "picture")
        index = predict.feature_names(PICTURE).index("bafta_film")
        self.assertEqual(nights[0]["nominees"][0]["features"][index], 0.0)
        self.assertEqual(nights[1]["nominees"][0]["features"][index], 1.0)


class Features(unittest.TestCase):
    def test_the_dga_winner_reaches_best_picture_through_the_film(self):
        rows = season(70, 1996)
        # The Directors Guild winner is recorded on the film here.
        nights = predict.build_nights({"nominations": rows}, {("dga", 1996): {"a"}}, "picture")
        index = predict.feature_names(PICTURE).index("dga")
        self.assertEqual([nominee["features"][index] for nominee in nights[0]["nominees"]], [1.0, 0.0])

    def test_nights_before_the_window_and_lone_entrants_are_left_out(self):
        rows = season(60, 1990) + [nomination("BEST PICTURE", 70, 1996, "a", True)]
        self.assertEqual(predict.build_nights({"nominations": rows}, {}, "picture"), [])

    def test_unofficial_rows_dont_join_the_field(self):
        rows = season(70, 1996) + [nomination("BEST PICTURE", 70, 1996, "c", competitive=False)]
        nights = predict.build_nights({"nominations": rows}, {}, "picture")
        self.assertEqual(len(nights[0]["nominees"]), 2)


class Calibration(unittest.TestCase):
    def test_bins_report_predicted_and_actual(self):
        results = [{"model": [0.9, 0.1], "winners": [True, False]}, {"model": [0.9, 0.1], "winners": [False, True]}]
        rows = predict.calibration(results)
        top = rows[-1]
        self.assertEqual((top["nominees"], top["predicted"], top["actual"]), (2, 0.9, 0.5))


class Views(unittest.TestCase):
    def test_night_view_names_the_pick_and_the_winner(self):
        view = predict.night_view({
            "ceremony": 90, "year": 2017, "labels": ["A", "B"], "model": [0.7, 0.3], "winners": [False, True],
        })
        self.assertEqual((view["pick"], view["winner"], view["correct"]), ("A", "B", False))
        self.assertEqual(view["winnerProbability"], 0.3)


if __name__ == "__main__":
    unittest.main()
