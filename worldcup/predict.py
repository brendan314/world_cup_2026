import copy
import re
from collections import defaultdict

from worldcup.normalize import score_parts


RANKING_SOURCE_URL = "https://inside.fifa.com/fifa-world-ranking/men"
RANKING_LAST_UPDATE = "11 June 2026"


# FIFA/Coca-Cola Men's World Ranking values pasted by the user from the FIFA page.
FIFA_RANKINGS = {
    "Argentina": {"rank": 1, "points": 1877.27},
    "Spain": {"rank": 2, "points": 1874.71},
    "France": {"rank": 3, "points": 1870.70},
    "England": {"rank": 4, "points": 1828.02},
    "Portugal": {"rank": 5, "points": 1767.85},
    "Brazil": {"rank": 6, "points": 1765.86},
    "Morocco": {"rank": 7, "points": 1755.10},
    "Netherlands": {"rank": 8, "points": 1753.57},
    "Belgium": {"rank": 9, "points": 1742.24},
    "Germany": {"rank": 10, "points": 1735.77},
    "Croatia": {"rank": 11, "points": 1714.87},
    "Colombia": {"rank": 13, "points": 1698.35},
    "Mexico": {"rank": 14, "points": 1687.48},
    "Senegal": {"rank": 15, "points": 1684.07},
    "Uruguay": {"rank": 16, "points": 1673.07},
    "United States": {"rank": 17, "points": 1671.23},
    "Japan": {"rank": 18, "points": 1661.58},
    "Switzerland": {"rank": 19, "points": 1650.06},
    "Iran": {"rank": 20, "points": 1619.58},
    "Turkey": {"rank": 22, "points": 1605.73},
    "Ecuador": {"rank": 23, "points": 1598.52},
    "Austria": {"rank": 24, "points": 1597.40},
    "South Korea": {"rank": 25, "points": 1591.63},
    "Australia": {"rank": 27, "points": 1579.34},
    "Algeria": {"rank": 28, "points": 1571.03},
    "Egypt": {"rank": 29, "points": 1562.37},
    "Canada": {"rank": 30, "points": 1559.48},
    "Norway": {"rank": 31, "points": 1557.44},
    "Ivory Coast": {"rank": 33, "points": 1540.87},
    "Panama": {"rank": 34, "points": 1539.16},
    "Sweden": {"rank": 38, "points": 1509.79},
    "Czech Republic": {"rank": 40, "points": 1505.74},
    "Paraguay": {"rank": 41, "points": 1505.35},
    "Scotland": {"rank": 42, "points": 1503.34},
    "Tunisia": {"rank": 45, "points": 1476.41},
    "DR Congo": {"rank": 46, "points": 1474.43},
    "Uzbekistan": {"rank": 50, "points": 1458.73},
    "Qatar": {"rank": 56, "points": 1450.31},
    "Iraq": {"rank": 57, "points": 1446.28},
    "South Africa": {"rank": 60, "points": 1428.38},
    "Saudi Arabia": {"rank": 61, "points": 1423.88},
    "Jordan": {"rank": 63, "points": 1387.74},
    "Bosnia and Herzegovina": {"rank": 64, "points": 1387.22},
    "Cape Verde": {"rank": 67, "points": 1371.11},
    "Ghana": {"rank": 73, "points": 1346.88},
    "Curaçao": {"rank": 82, "points": 1294.77},
    "Haiti": {"rank": 83, "points": 1293.10},
    "New Zealand": {"rank": 85, "points": 1275.58},
}


GROUP_RE = re.compile(r"^Group ([A-L])$")
QUALIFIER_RE = re.compile(r"^(Winner|Runner-up) Group ([A-L])$")
THIRD_RE = re.compile(r"^3rd Group ([A-L](?:/[A-L])*)$")
MATCH_REF_RE = re.compile(r"^(Winner|Loser) Match (\d+)$")


def ranking_for(team):
    return FIFA_RANKINGS.get(team, {"rank": 999, "points": 0})


def _ranking_sort_value(team):
    ranking = ranking_for(team)
    return (ranking["rank"], -ranking["points"], team)


def _empty_record(team, group):
    ranking = ranking_for(team)
    return {
        "team": team,
        "group": group,
        "played": 0,
        "points": 0,
        "goal_difference": 0,
        "goals_for": 0,
        "rank": ranking["rank"],
        "ranking_points": ranking["points"],
    }


def _apply_result(record_1, record_2, goals_1, goals_2):
    record_1["played"] += 1
    record_2["played"] += 1
    record_1["goals_for"] += goals_1
    record_2["goals_for"] += goals_2
    record_1["goal_difference"] += goals_1 - goals_2
    record_2["goal_difference"] += goals_2 - goals_1

    if goals_1 > goals_2:
        record_1["points"] += 3
    elif goals_2 > goals_1:
        record_2["points"] += 3
    else:
        record_1["points"] += 1
        record_2["points"] += 1


def _predicted_group_score(team_1, team_2):
    rank_1 = ranking_for(team_1)["rank"]
    rank_2 = ranking_for(team_2)["rank"]
    if rank_1 == rank_2:
        return 1, 1
    if rank_1 < rank_2:
        return 2, 0
    return 0, 2


def _standing_key(record):
    return (
        -record["points"],
        -record["goal_difference"],
        -record["goals_for"],
        record["rank"],
        record["team"],
    )


def predicted_group_standings(matches):
    records = defaultdict(dict)

    for match in matches:
        group_match = GROUP_RE.match(match.get("stage", ""))
        if not group_match:
            continue
        group = group_match.group(1)
        for key in ("team_1", "team_2"):
            team = match.get(key, "")
            records[group].setdefault(team, _empty_record(team, group))

        parts = score_parts(match.get("score"))
        if parts:
            goals_1, goals_2 = parts
        else:
            goals_1, goals_2 = _predicted_group_score(match["team_1"], match["team_2"])
        _apply_result(records[group][match["team_1"]], records[group][match["team_2"]], goals_1, goals_2)

    return {group: sorted(group_records.values(), key=_standing_key) for group, group_records in records.items()}


def _qualified_third_groups(standings):
    third_records = [records[2] for records in standings.values() if len(records) >= 3]
    return {
        record["group"]: record
        for record in sorted(third_records, key=_standing_key)[:8]
    }


def _display_prediction(team, prediction):
    if not prediction or prediction == team:
        return {"label": team, "probable": False, "rank": ranking_for(team)["rank"]}
    return {
        "label": prediction,
        "original": team,
        "probable": True,
        "rank": ranking_for(prediction)["rank"],
    }


def _assign_match_numbers(knockout_matches):
    for offset, match in enumerate(knockout_matches, start=73):
        if not match.get("match_number"):
            match["match_number"] = offset


def _resolve_seed(seed, standings, third_assignments, match_results):
    qualifier = QUALIFIER_RE.match(seed)
    if qualifier:
        position = 0 if qualifier.group(1) == "Winner" else 1
        group = qualifier.group(2)
        records = standings.get(group, [])
        return records[position]["team"] if len(records) > position else None

    third = THIRD_RE.match(seed)
    if third:
        eligible_groups = third.group(1).split("/")
        chosen = third_assignments.get(seed)
        if chosen:
            return chosen["team"]
        ranked_options = [
            standings[group][2]
            for group in eligible_groups
            if group in standings and len(standings[group]) >= 3
        ]
        return sorted(ranked_options, key=_standing_key)[0]["team"] if ranked_options else None

    match_ref = MATCH_REF_RE.match(seed)
    if match_ref:
        kind, number = match_ref.group(1), int(match_ref.group(2))
        result = match_results.get(number, {})
        return result.get("winner" if kind == "Winner" else "loser")

    return seed if seed in FIFA_RANKINGS else None


def _assign_third_place_slots(knockout_matches, standings):
    qualified = _qualified_third_groups(standings)
    used_groups = set()
    assignments = {}

    for match in knockout_matches:
        for seed in (match.get("team_1", ""), match.get("team_2", "")):
            third = THIRD_RE.match(seed)
            if not third:
                continue
            eligible = third.group(1).split("/")
            options = [
                qualified[group]
                for group in eligible
                if group in qualified and group not in used_groups
            ]
            if not options:
                options = [
                    standings[group][2]
                    for group in eligible
                    if group in standings and len(standings[group]) >= 3 and group not in used_groups
                ]
            if options:
                chosen = sorted(options, key=_standing_key)[0]
                assignments[seed] = chosen
                used_groups.add(chosen["group"])

    return assignments


def enrich_predictions(matches):
    enriched = copy.deepcopy(matches)
    standings = predicted_group_standings(enriched)
    knockout_matches = [match for match in enriched if not match.get("stage", "").startswith("Group ")]
    _assign_match_numbers(knockout_matches)
    third_assignments = _assign_third_place_slots(knockout_matches, standings)
    match_results = {}

    for match in knockout_matches:
        prediction_1 = _resolve_seed(match.get("team_1", ""), standings, third_assignments, match_results)
        prediction_2 = _resolve_seed(match.get("team_2", ""), standings, third_assignments, match_results)
        match["team_1_prediction"] = _display_prediction(match.get("team_1", ""), prediction_1)
        match["team_2_prediction"] = _display_prediction(match.get("team_2", ""), prediction_2)

        if prediction_1 and prediction_2:
            winner = min((prediction_1, prediction_2), key=_ranking_sort_value)
            loser = prediction_2 if winner == prediction_1 else prediction_1
            match["predicted_winner"] = winner
            match["predicted_winner_rank"] = ranking_for(winner)["rank"]
            match_results[match["match_number"]] = {"winner": winner, "loser": loser}

    return {
        "matches": enriched,
        "group_standings": standings,
        "prediction_metadata": {
            "source_url": RANKING_SOURCE_URL,
            "source_name": "FIFA/Coca-Cola Men's World Ranking",
            "last_update": RANKING_LAST_UPDATE,
            "logic_notes": [
                "Unplayed group matches are predicted by FIFA ranking, with a 2-0 result for the higher-ranked team.",
                "Group tables use points, goal difference, goals scored, then FIFA ranking as the final tie-breaker.",
                "Best third-place slots are approximate because the official Round of 32 mapping depends on which groups produce the eight third-place qualifiers.",
                "Knockout winners are predicted by FIFA ranking when the actual teams are not known.",
            ],
        },
    }
