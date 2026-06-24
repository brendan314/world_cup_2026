import unittest

from worldcup.predict import enrich_predictions, predicted_group_standings, ranking_for


class PredictTest(unittest.TestCase):
    def test_ranking_aliases_match_fixture_names(self):
        self.assertEqual(ranking_for("United States")["rank"], 17)
        self.assertEqual(ranking_for("Turkey")["rank"], 22)
        self.assertEqual(ranking_for("Ivory Coast")["rank"], 33)
        self.assertEqual(ranking_for("DR Congo")["rank"], 46)
        self.assertEqual(ranking_for("Cape Verde")["rank"], 67)
        self.assertEqual(ranking_for("South Korea")["rank"], 25)

    def test_group_standings_use_played_results_before_rankings(self):
        matches = [
            {
                "stage": "Group A",
                "team_1": "Mexico",
                "team_2": "South Africa",
                "score": "0-1",
            },
            {
                "stage": "Group A",
                "team_1": "Mexico",
                "team_2": "Czech Republic",
                "score": "",
            },
        ]

        standings = predicted_group_standings(matches)

        self.assertEqual(standings["A"][0]["team"], "Mexico")
        self.assertEqual(standings["A"][1]["team"], "South Africa")

    def test_knockout_predictions_resolve_match_references(self):
        matches = [
            {"stage": "Group A", "team_1": "Argentina", "team_2": "Haiti", "score": ""},
            {"stage": "Group B", "team_1": "France", "team_2": "Ghana", "score": ""},
            {
                "stage": "Round of 32",
                "team_1": "Winner Group A",
                "team_2": "Runner-up Group B",
                "match_number": 73,
            },
            {
                "stage": "Round of 16",
                "team_1": "Winner Match 73",
                "team_2": "Brazil",
                "match_number": 89,
            },
        ]

        predictions = enrich_predictions(matches)["matches"]

        self.assertEqual(predictions[2]["team_1_prediction"]["label"], "Argentina")
        self.assertEqual(predictions[2]["predicted_winner"], "Argentina")
        self.assertEqual(predictions[3]["team_1_prediction"]["label"], "Argentina")
        self.assertEqual(predictions[3]["predicted_winner"], "Argentina")


if __name__ == "__main__":
    unittest.main()
