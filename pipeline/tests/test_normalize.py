"""One test per source quirk. Quirk 9 (upstream update lag) is handled by the Phase 6 season file."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import normalize as nz  # noqa: E402
import story  # noqa: E402
import validate  # noqa: E402

HEADER = "Ceremony\tYear\tClass\tCanonicalCategory\tCategory\tFilm\tFilmId\tName\tNominees\tNomineeIds\tWinner\tDetail\tNote\tCitation\n"


def row(**overrides):
    base = {
        "Ceremony": "1",
        "Year": "1927/28",
        "Class": "Acting",
        "CanonicalCategory": "ACTOR IN A LEADING ROLE",
        "Category": "ACTOR",
        "Film": "A Film",
        "FilmId": "tt0000001",
        "Name": "A Person",
        "Nominees": "A Person",
        "NomineeIds": "nm0000001",
        "Winner": "",
        "Detail": "",
        "Note": "",
        "Citation": "",
    }
    return {**base, **overrides}


class SourceQuirks(unittest.TestCase):
    def test_1_tab_separated_rows_with_missing_trailing_columns(self):
        line = "1\t1927/28\tActing\tACTOR IN A LEADING ROLE\tACTOR\tA Film\ttt0000001\tA Person\tA Person\tnm0000001\n"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.tsv"
            path.write_text(HEADER + line, encoding="utf-8")
            rows = nz.read_rows(path)
        self.assertEqual(rows[0]["Winner"], "")
        self.assertEqual(rows[0]["Citation"], "")
        self.assertFalse(nz.parse_nomination(rows[0])["winner"])

    def test_1b_backslash_escaped_quotes_are_unescaped(self):
        line = '1\t1927/28\tTitle\tBEST PICTURE\tBEST PICTURE\t"Children No More: \\"Were and Are Gone\\""\ttt0000001\n'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.tsv"
            path.write_text(HEADER + line, encoding="utf-8")
            rows = nz.read_rows(path)
        self.assertEqual(rows[0]["Film"], 'Children No More: "Were and Are Gone"')

    def test_2_winner_flag_accepts_only_true_or_blank(self):
        self.assertTrue(nz.parse_winner("True"))
        self.assertFalse(nz.parse_winner(""))
        with self.assertRaises(ValueError):
            nz.parse_winner("False")

    def test_3_placeholder_ids_become_separate_people(self):
        nominees = nz.parse_nominees(row(Nominees="Charlie Kaufman|Donald Kaufman", NomineeIds="nm0442109|?"))
        self.assertEqual(nominees[1]["id"], "unk-donald-kaufman")
        self.assertEqual(nominees[1]["type"], "unknown")
        other = nz.parse_nominees(row(Nominees="Someone Else", NomineeIds="?"))
        self.assertNotEqual(other[0]["id"], nominees[1]["id"])

    def test_4_company_ids_are_a_separate_type(self):
        nominee = nz.parse_nominees(row(Nominees="Metro-Goldwyn-Mayer", NomineeIds="co0007143"))[0]
        self.assertEqual(nominee["type"], "company")

    def test_5_non_competitive_rows_stay_out_of_competitive_totals(self):
        rows = [
            row(Winner="True"),
            row(Class="Special", CanonicalCategory="HONORARY AWARD", Category="HONORARY AWARD", Winner="True"),
        ]
        person = nz.normalize(rows)["people"][0]
        self.assertEqual((person["nominations"], person["wins"], person["honors"]), (1, 1, 1))

    def test_6_category_drift_maps_to_families_and_fails_on_unknown(self):
        self.assertEqual(nz.category_family(row(Class="Production", CanonicalCategory="CINEMATOGRAPHY (Color)")), "Cinematography")
        with self.assertRaises(ValueError):
            nz.category_family(row(CanonicalCategory="BEST VIBES"))

    def test_7_multi_value_cells_split_and_must_align(self):
        films = nz.parse_films(row(Film="One|Two", FilmId="tt0000001|tt0000002"))
        self.assertEqual([film["id"] for film in films], ["tt0000001", "tt0000002"])
        with self.assertRaises(ValueError):
            nz.parse_films(row(Film="One|Two", FilmId="tt0000001"))
        with self.assertRaises(ValueError):
            nz.parse_nominees(row(Nominees="One|Two", NomineeIds="nm0000001"))

    def test_8_ceremony_number_is_the_key_for_split_years(self):
        data = nz.normalize([row(Year="1927/28", Ceremony="1"), row(Year="1928", Ceremony="2")])
        self.assertEqual([ceremony["ceremony"] for ceremony in data["ceremonies"]], [1, 2])


class UnofficialRows(unittest.TestCase):
    NOTE = "NOTE: THIS IS NOT AN OFFICIAL NOMINATION. Write-in candidate."

    def test_they_count_for_nothing(self):
        rows = [row(), row(Note=self.NOTE, Ceremony="2", Year="1928")]
        data = nz.normalize(rows)
        self.assertEqual((data["people"][0]["nominations"], data["people"][0]["honors"]), (1, 0))
        self.assertEqual(data["films"][0]["nominations"], 1)

    def test_a_winner_under_the_same_note_still_counts(self):
        data = nz.normalize([row(Note=self.NOTE, Winner="True")])
        self.assertEqual((data["people"][0]["nominations"], data["people"][0]["wins"]), (1, 1))

    def test_their_category_stays_competitive(self):
        nomination = nz.parse_nomination(row(Note=self.NOTE))
        self.assertFalse(nomination["competitive"])
        self.assertTrue(nomination["inCompetitiveCategory"])
        self.assertEqual(nz.normalize([row(Note=self.NOTE)])["categories"][0]["competitive"], True)


class EdgeCases(unittest.TestCase):
    def test_film_without_an_id_gets_a_synthetic_one(self):
        films = nz.parse_films(row(Film="Letter from Livingston", FilmId=""))
        self.assertEqual(films[0]["id"], "unk-letter-from-livingston")

    def test_row_with_name_but_no_nominee_columns_keeps_the_name(self):
        nominees = nz.parse_nominees(row(Name="Some Studio", Nominees="", NomineeIds=""))
        self.assertEqual(nominees[0]["id"], "unk-some-studio")

    def test_row_with_no_people_at_all_is_allowed(self):
        self.assertEqual(nz.parse_nominees(row(Name="", Nominees="", NomineeIds="")), [])

    def test_unexpected_id_prefix_fails(self):
        with self.assertRaises(ValueError):
            nz.entity_type("xx123")

    def test_two_nominees_on_one_film_count_as_two_film_nominations(self):
        rows = [row(), row(Nominees="B Person", NomineeIds="nm0000002", Name="B Person")]
        self.assertEqual(nz.normalize(rows)["films"][0]["nominations"], 2)


class Validation(unittest.TestCase):
    def test_two_best_picture_winners_are_rejected(self):
        winner = {"ceremony": 1, "category": "BEST PICTURE", "winner": True}
        data = {"ceremonies": [{"ceremony": 1}], "nominations": [winner, winner]}
        self.assertEqual(len(list(validate.check_best_picture(data))), 1)

    def test_winner_without_links_is_rejected(self):
        winner = {"ceremony": 1, "category": "X", "winner": True, "films": [], "nominees": [], "competitive": True, "citation": "To someone"}
        self.assertEqual(len(list(validate.check_winner_links({"nominations": [winner]}))), 1)

    def test_honor_naming_its_recipient_only_in_the_citation_is_allowed(self):
        honor = {"ceremony": 86, "category": "X", "winner": True, "films": [], "nominees": [], "competitive": False, "citation": "To all those"}
        self.assertEqual(list(validate.check_winner_links({"nominations": [honor]})), [])
        self.assertEqual(len(list(validate.check_winner_links({"nominations": [{**honor, "citation": ""}]}))), 1)

    def test_placeholder_reaching_output_is_rejected(self):
        data = {"people": [{"id": "?"}], "nominations": []}
        self.assertEqual(len(list(validate.check_placeholder_ids(data))), 1)


class Meta(unittest.TestCase):
    def test_split_first_year_is_read_as_its_first_year(self):
        meta = story.build_meta([{"filmYear": "1927/28"}, {"filmYear": "2025"}])
        self.assertEqual(meta, {"ceremonies": 2, "firstFilmYear": 1927, "lastFilmYear": 2025})


class SweepStory(unittest.TestCase):
    def film(self, film_id, nominations, wins):
        return {"id": film_id, "title": film_id, "filmYear": "2000", "firstCeremony": 73, "nominations": nominations, "wins": wins}

    def test_totals_grid_and_perfect_list(self):
        films = [self.film("a", 1, 0), self.film("b", 1, 0), self.film("c", 5, 5), self.film("d", 0, 0)]
        sweep = story.build_sweep(films)
        self.assertEqual(sweep["totals"]["films"], 3)
        self.assertEqual(sweep["totals"]["emptyHanded"], 2)
        self.assertEqual(next(cell for cell in sweep["grid"] if cell["nominations"] == 1)["count"], 2)
        self.assertEqual([film["id"] for film in sweep["perfect"]], ["c"])

    def test_summaries_never_publish_private_fields(self):
        film = {**self.film("a", 1, 0), "private": {"imdbRating": 9.0}}
        self.assertEqual(set(story.film_summary(film)), {"id", "title", "year", "poster"})

    def test_crowded_cells_are_capped_but_counted(self):
        films = [self.film(f"f{i}", 1, 0) for i in range(story.MAX_FILMS_PER_CELL + 5)]
        cell = story.build_sweep(films)["grid"][0]
        self.assertEqual(cell["count"], story.MAX_FILMS_PER_CELL + 5)
        self.assertEqual(len(cell["films"]), story.MAX_FILMS_PER_CELL)


if __name__ == "__main__":
    unittest.main()
