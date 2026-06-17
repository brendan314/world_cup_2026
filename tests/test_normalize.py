import unittest

from worldcup.normalize import (
    convert_to_timezone,
    normalize_date,
    normalize_score,
    status_from_score,
    winner_from_score,
)


class NormalizeTest(unittest.TestCase):
    def test_normalize_date(self):
        self.assertEqual(normalize_date("June 11, 2026"), "2026-06-11")

    def test_normalize_score_accepts_en_dash(self):
        self.assertEqual(normalize_score("2–0"), "2-0")

    def test_normalize_score_ignores_match_number(self):
        self.assertEqual(normalize_score("Match 31"), "")

    def test_status_from_score(self):
        self.assertEqual(status_from_score("1-1"), "played")
        self.assertEqual(status_from_score(""), "scheduled")

    def test_winner_from_score(self):
        self.assertEqual(winner_from_score("2-0"), "team_1")
        self.assertEqual(winner_from_score("0-1"), "team_2")
        self.assertEqual(winner_from_score("1-1"), "draw")

    def test_convert_to_dublin_timezone(self):
        converted = convert_to_timezone("2026-06-11", "1:00 p.m. UTC−6", "Europe/Dublin")

        self.assertEqual(converted["date"], "2026-06-11")
        self.assertEqual(converted["time"], "20:00")
        self.assertEqual(converted["timezone_note"], "Europe/Dublin")


if __name__ == "__main__":
    unittest.main()
