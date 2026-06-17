import re

import os

import requests
from bs4 import BeautifulSoup

from worldcup.normalize import (
    clean_text,
    convert_to_timezone,
    normalize_date,
    normalize_score,
    sort_key,
    status_from_score,
    winner_from_score,
)


SOURCE_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"
HEADERS = {
    "User-Agent": "try-world-cup-fixtures/1.0 (personal project; reads public Wikipedia HTML)"
}


def fetch_html(url=SOURCE_URL):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def _text_from(node, selector):
    found = node.select_one(selector)
    return clean_text(found.get_text(" ", strip=True)) if found else ""


def _stage_for(box):
    heading = box.find_previous(["h2", "h3", "h4"])
    while heading:
        stage = clean_text(heading.get_text(" ", strip=True))
        if re.match(r"Group [A-L]$", stage):
            return stage
        if stage in {
            "Round of 32",
            "Round of 16",
            "Quarter-finals",
            "Quarterfinals",
            "Semi-finals",
            "Semifinals",
            "Match for third place",
            "Third place",
            "Final",
        }:
            return stage.replace("Quarter-finals", "Quarterfinals").replace("Semi-finals", "Semifinals")
        heading = heading.find_previous(["h2", "h3", "h4"])
    return "Unknown"


def _match_number(score_cell_text):
    match = re.search(r"Match\s+(\d+)", score_cell_text)
    return int(match.group(1)) if match else None


def parse_matches(html, source_url=SOURCE_URL):
    soup = BeautifulSoup(html, "lxml")
    matches = []
    display_timezone = os.getenv("WORLD_CUP_DISPLAY_TIMEZONE", "Europe/Dublin")

    for box in soup.select("div.footballbox"):
        source_date = _text_from(box, ".fdate .bday") or normalize_date(_text_from(box, ".fdate"))
        source_time = _text_from(box, ".ftime")
        display_time = convert_to_timezone(source_date, source_time, display_timezone)
        team_1 = _text_from(box, ".fhome [itemprop='name']") or _text_from(box, ".fhome")
        team_2 = _text_from(box, ".faway [itemprop='name']") or _text_from(box, ".faway")
        score_cell = _text_from(box, ".fscore")
        score = normalize_score(score_cell)
        venue = _text_from(box, ".fright [itemprop='name address']")
        stage = _stage_for(box)

        if not team_1 or not team_2:
            continue

        matches.append(
            {
                "date": display_time["date"],
                "time": display_time["time"],
                "timezone_note": display_time["timezone_note"],
                "source_date": source_date,
                "source_time": source_time,
                "stage": stage,
                "team_1": team_1,
                "team_2": team_2,
                "score": score,
                "venue": venue,
                "status": status_from_score(score),
                "winner": winner_from_score(score),
                "match_number": _match_number(score_cell),
                "source_url": source_url,
            }
        )

    return sorted(matches, key=sort_key)


def scrape_matches():
    return parse_matches(fetch_html())
