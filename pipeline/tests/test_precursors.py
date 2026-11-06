import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fetch_precursors as fp  # noqa: E402


class RowYear(unittest.TestCase):
    def test_reads_the_common_layouts(self):
        for line in (
            "| 1995",
            '| rowspan="5" style="text-align:center;" | 1995<br>(48th)',
            '! rowspan="5" style="text-align:center;" | [[53rd Golden Globe Awards|1995]]',
            "| [[1995 in film|1995]]",
            "| {{center|'''1995'''<br>{{small|([[49th British Academy Film Awards|49th]])}}}}",
            """| rowspan="6" align="center" , | '''1995'''<br>{{small|([[49th British Academy Film Awards|49th]])}}""",
        ):
            self.assertEqual(fp.row_year(line), 1995, line)

    def test_a_film_titled_with_a_number_is_not_a_year(self):
        for line in (
            "| '''''[[1917 (2019 film)|1917]]'''''",
            "| ''[[1917 (2019 film)|1917]]''",
            "| ''[[2001: A Space Odyssey]]''",
            "| [[2001: A Space Odyssey]]",
            "| [[2012 Olympics]]",
        ):
            self.assertIsNone(fp.row_year(line), line)

    def test_ignores_rows_that_only_mention_a_year(self):
        for line in (
            "| ''[[The Magic Box]]'' (1951)",
            "| [[Les Misérables (2012 film)|Les Misérables]]",
            "|-",
            "|}",
            "* 2019 - something",
        ):
            self.assertIsNone(fp.row_year(line), line)


class Winners(unittest.TestCase):
    PAGE = """{| class="wikitable"
|-
! Year !! Film
|-
| rowspan="2" | 2019
| '''''[[1917 (2019 film)|1917]]'''''
|-
| ''[[The Irishman]]''
|-
| rowspan="2" | 2020
| '''''[[Nomadland (film)|Nomadland]]'''''
|-
| ''[[Mank]]''
|}"""

    def test_a_film_named_like_a_year_survives(self):
        found = fp.winners_by_year(self.PAGE)
        self.assertEqual(found[2019], ["1917"])

    def test_the_rows_own_bold_year_is_not_a_winner(self):
        found = fp.winners_by_year("{|\n|-\n| {{center|'''1947'''}}\n| '''''[[Hamlet]]'''''\n|}")
        self.assertEqual(found[1947], ["Hamlet"])

    def test_nominees_in_plain_text_are_not_winners(self):
        found = fp.winners_by_year(self.PAGE)
        self.assertNotIn("The Irishman", found[2019])
        self.assertEqual(found[2020], ["Nomadland"])

    def test_notes_and_refs_dont_leak_in(self):
        self.assertEqual(fp.plain("[[Parasite (2019 film)|Parasite]]<ref name=x>note</ref>"), "Parasite")


class Matching(unittest.TestCase):
    def nomination(self, film, person):
        return {"films": [{"id": film, "title": film}], "nominees": [{"id": person, "name": person}]}

    def test_whole_words_only(self):
        self.assertTrue(fp.contains_name("up", "up"))
        self.assertFalse(fp.contains_name("up in the air", "up "))
        self.assertFalse(fp.contains_name("supper", "up"))

    def test_accents_and_case_dont_matter(self):
        self.assertEqual(fp.fold("Chloé  ZHAO!"), "chloe zhao")

    def test_a_person_with_two_films_counts_once(self):
        nominees = [self.nomination("Traffic", "Steven Soderbergh"), self.nomination("Erin Brockovich", "Steven Soderbergh")]
        self.assertEqual(fp.match_winners(["Steven Soderbergh"], nominees, False), [("Steven Soderbergh", "Steven Soderbergh")])

    def test_a_name_in_a_different_order_still_matches(self):
        nominees = [self.nomination("Minari", "Yuh-Jung Youn")]
        self.assertEqual(fp.match_winners(["Youn Yuh-jung", "Minari"], nominees, False), [("Yuh-Jung Youn", "Yuh-Jung Youn")])

    def test_a_written_out_middle_name_still_matches(self):
        nominees = [self.nomination("The Revenant", "Alejandro G. Iñárritu")]
        matched = fp.match_winners(["Alejandro González Iñárritu", "The Revenant"], nominees, False)
        self.assertEqual([name for _, name in matched], ["Alejandro G. Iñárritu"])

    def test_different_people_who_share_a_first_and_last_word_need_a_middle_name(self):
        nominees = [self.nomination("A", "Robert De Niro")]
        self.assertEqual(fp.match_winners(["Robert Niro"], nominees, False), [])

    def test_a_short_film_title_matches_its_long_form(self):
        nominees = [self.nomination("Birdman or (The Unexpected Virtue of Ignorance)", "a")]
        self.assertEqual(len(fp.match_winners(["Birdman"], nominees, True)), 1)

    def test_a_subtitle_short_form_needs_two_words(self):
        self.assertEqual(fp.film_names("Precious: Based on the Novel Push"), ["Precious: Based on the Novel Push"])
        self.assertEqual(fp.film_names("Mad Max: Fury Road"), ["Mad Max: Fury Road", "Mad Max"])

    def test_word_order_is_only_forgiven_for_people(self):
        nominees = [self.nomination("Road House", "a")]
        self.assertEqual(fp.match_winners(["House Road"], nominees, True), [])

    def test_a_tie_keeps_both(self):
        nominees = [self.nomination("Gravity", "a"), self.nomination("12 Years a Slave", "b"), self.nomination("Her", "c")]
        matched = fp.match_winners(["Gravity", "12 Years a Slave"], nominees, True)
        self.assertEqual([name for _, name in matched], ["Gravity", "12 Years a Slave"])

    def test_a_winner_the_academy_skipped_matches_nobody(self):
        self.assertEqual(fp.match_winners(["Someone Else"], [self.nomination("A", "b")], False), [])


if __name__ == "__main__":
    unittest.main()
