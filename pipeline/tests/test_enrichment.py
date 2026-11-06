import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import coverage  # noqa: E402
import enrich  # noqa: E402
import fetch_cpi  # noqa: E402
import fetch_imdb  # noqa: E402
import fetch_tmdb  # noqa: E402
import fetch_wikidata  # noqa: E402


class Imdb(unittest.TestCase):
    def test_missing_marker_becomes_none(self):
        row = {"titleType": "movie", "startYear": "\\N", "runtimeMinutes": "\\N", "genres": "\\N"}
        self.assertEqual(fetch_imdb.film_basics(row), {"titleType": "movie", "startYear": None, "runtime": None, "genres": []})

    def test_genres_split(self):
        row = {"titleType": "movie", "startYear": "1997", "runtimeMinutes": "194", "genres": "Drama,Romance"}
        self.assertEqual(fetch_imdb.film_basics(row)["genres"], ["Drama", "Romance"])

    def test_stray_quotes_do_not_swallow_following_rows(self):
        text = 'tconst\tprimaryTitle\ntt1\t"Unbalanced title\ntt2\tNext\n'
        rows = list(fetch_imdb.read_rows(io.StringIO(text)))
        self.assertEqual([row["tconst"] for row in rows], ["tt1", "tt2"])


class Tmdb(unittest.TestCase):
    def test_zero_money_means_unknown(self):
        summary = fetch_tmdb.summarize_movie({"id": 1, "budget": 0, "revenue": 0, "release_date": ""})
        self.assertIsNone(summary["budget"])
        self.assertIsNone(summary["revenue"])
        self.assertIsNone(summary["releaseDate"])

    def test_real_money_and_lists_are_kept(self):
        summary = fetch_tmdb.summarize_movie({
            "id": 597, "budget": 200, "revenue": 900, "poster_path": "/p.jpg", "original_language": "en",
            "production_countries": [{"iso_3166_1": "US"}], "production_companies": [{"name": "Paramount"}],
        })
        self.assertEqual((summary["budget"], summary["revenue"], summary["poster"]), (200, 900, "/p.jpg"))
        self.assertEqual((summary["countries"], summary["companies"]), (["US"], ["Paramount"]))


class Wikidata(unittest.TestCase):
    def binding(self, imdb, **values):
        return {"imdb": {"value": imdb}, **{key: {"value": value} for key, value in values.items()}}

    def test_rows_collapse_per_person(self):
        rows = [
            self.binding("nm1", birth="1907-05-12T00:00:00Z", genderLabel="female", countryLabel="United States"),
            self.binding("nm1", birth="1907-05-12T00:00:00Z", genderLabel="female", countryLabel="Canada"),
        ]
        person = fetch_wikidata.summarize(rows)["nm1"]
        self.assertEqual(person["birthDates"], ["1907-05-12"])
        self.assertEqual(person["countries"], ["Canada", "United States"])

    def test_unknown_value_placeholders_are_dropped(self):
        rows = [self.binding("nm1", birth="http://www.wikidata.org/.well-known/genid/abc", genderLabel="t12345", countryLabel="Q30")]
        person = fetch_wikidata.summarize(rows)["nm1"]
        self.assertEqual((person["birthDates"], person["genders"], person["countries"]), ([], [], []))


class Cpi(unittest.TestCase):
    def test_incomplete_years_and_missing_values_are_skipped(self):
        rows = [{"observation_date": f"2000-{month:02d}-01", "CPIAUCNS": "100"} for month in range(1, 13)]
        rows += [{"observation_date": "2001-01-01", "CPIAUCNS": "101"}, {"observation_date": "2001-02-01", "CPIAUCNS": "."}]
        self.assertEqual(fetch_cpi.annual_averages(rows), {2000: 100.0})


class Merge(unittest.TestCase):
    def test_film_merge_handles_a_film_missing_from_sources(self):
        film = enrich.merge_film({"id": "tt1", "title": "A"}, {}, {})
        self.assertIsNone(film["rating"])
        self.assertEqual(film["genres"], [])

    def test_birth_date_prefers_the_one_agreeing_with_imdb(self):
        self.assertEqual(enrich.choose_birth_date(["1900-01-01", "1905-06-07"], 1905), "1905-06-07")
        self.assertEqual(enrich.choose_birth_date(["1900-01-01", "1905-06-07"], None), "1900-01-01")
        self.assertIsNone(enrich.choose_birth_date([], 1905))

    def test_gender_with_several_or_unmapped_values_stays_unknown(self):
        self.assertEqual(enrich.choose_gender(["female"]), "woman")
        self.assertEqual(enrich.choose_gender(["trans woman"]), "woman")
        self.assertIsNone(enrich.choose_gender(["female", "male"]))
        self.assertIsNone(enrich.choose_gender(["non-binary"]))
        self.assertIsNone(enrich.choose_gender([]))

    def test_companies_are_not_enriched(self):
        company = {"id": "co1", "type": "company", "name": "MGM"}
        self.assertEqual(enrich.merge_person(company, {}, {}), company)

    def test_imdb_values_are_never_published_as_birth_year(self):
        person = {"id": "nm1", "type": "person", "name": "A"}
        merged = enrich.merge_person(person, {"nm1": {"birthYear": 1950}}, {})
        self.assertIsNone(merged["birthYear"])

    def test_film_ratings_come_from_tmdb_and_imdb_stays_private(self):
        film = enrich.merge_film(
            {"id": "tt1", "title": "A"},
            {"tt1": {"rating": 9.0, "votes": 500, "titleType": "movie"}},
            {"tt1": {"rating": 7.0, "votes": 40, "genres": ["Drama"]}},
        )
        self.assertEqual((film["rating"], film["votes"], film["genres"]), (7.0, 40, ["Drama"]))
        self.assertEqual(film["private"]["imdbRating"], 9.0)

    def test_inflation_adjustment(self):
        cpi = {1950: 25.0, 2025: 300.0}
        self.assertEqual(enrich.adjust_for_inflation(100, 1950, cpi), 1200.0)
        self.assertIsNone(enrich.adjust_for_inflation(None, 1950, cpi))
        self.assertIsNone(enrich.adjust_for_inflation(100, 1900, cpi))


class Coverage(unittest.TestCase):
    def test_table_counts_empty_lists_and_none_as_missing(self):
        items = [{"group": "a", "x": 1, "y": []}, {"group": "a", "x": None, "y": ["z"]}]
        rows = coverage.coverage_table(items, ["x", "y"], lambda item: item["group"])
        self.assertEqual(rows[0], ["a", 2, 50.0, 50.0])
        self.assertEqual(rows[-1][0], "All")

    def test_zero_is_a_real_value(self):
        self.assertTrue(coverage.is_filled(0))


if __name__ == "__main__":
    unittest.main()
