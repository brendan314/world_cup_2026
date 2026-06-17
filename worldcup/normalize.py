import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


SCORE_RE = re.compile(r"^\d+\s*[-–]\s*\d+(?:\s*\([^)]+\))?$")
TIME_RE = re.compile(
    r"(?P<hour>\d{1,2}):(?P<minute>\d{2})\s*(?P<period>a\.m\.|p\.m\.)\s*UTC(?P<sign>[+\-−])(?P<offset>\d{1,2})",
    re.IGNORECASE,
)


def clean_text(value):
    if not value:
        return ""
    value = " ".join(value.replace("\xa0", " ").split())
    return value.replace(" ,", ",")


def normalize_date(value):
    value = clean_text(value)
    match = re.search(r"([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})", value)
    if not match:
        return value
    month_name, day, year = match.groups()
    month = MONTHS.get(month_name)
    if not month:
        return value
    return datetime(int(year), month, int(day)).date().isoformat()


def normalize_score(value):
    value = clean_text(value).replace("–", "-")
    if SCORE_RE.match(value):
        return re.sub(r"\s+", "", value)
    return ""


def score_parts(score):
    match = re.match(r"^(\d+)-(\d+)", score or "")
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def winner_from_score(score):
    parts = score_parts(score)
    if not parts:
        return ""
    home, away = parts
    if home > away:
        return "team_1"
    if away > home:
        return "team_2"
    return "draw"


def status_from_score(score):
    return "played" if score else "scheduled"


def convert_to_timezone(date_value, time_value, timezone_name="Europe/Dublin"):
    match = TIME_RE.search(clean_text(time_value))
    if not date_value or not match:
        return {
            "date": date_value,
            "time": clean_text(time_value),
            "timezone_note": "local venue time",
        }

    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    period = match.group("period").lower()
    if period == "p.m." and hour != 12:
        hour += 12
    if period == "a.m." and hour == 12:
        hour = 0

    sign = -1 if match.group("sign") in {"-", "−"} else 1
    source_tz = timezone(timedelta(hours=sign * int(match.group("offset"))))
    source_dt = datetime.fromisoformat(date_value).replace(hour=hour, minute=minute, tzinfo=source_tz)
    target_dt = source_dt.astimezone(ZoneInfo(timezone_name))

    return {
        "date": target_dt.date().isoformat(),
        "time": target_dt.strftime("%H:%M"),
        "timezone_note": timezone_name,
    }


def sort_key(match):
    return (match.get("date") or "", match.get("time") or "", match.get("team_1") or "")
