import json
import os
from datetime import datetime, timezone
from pathlib import Path

from worldcup.scrape import SOURCE_URL, scrape_matches


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_FILE = DATA_DIR / "matches.json"
DEFAULT_TTL_SECONDS = 60 * 60 * 3


def _ttl_seconds():
    raw = os.getenv("WORLD_CUP_CACHE_TTL_SECONDS", str(DEFAULT_TTL_SECONDS))
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_TTL_SECONDS


def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_cache():
    if not CACHE_FILE.exists():
        return None
    with CACHE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_cache(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _is_stale(data):
    refreshed_at = data.get("metadata", {}).get("refreshed_at")
    if not refreshed_at:
        return True
    try:
        refreshed = datetime.fromisoformat(refreshed_at)
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - refreshed).total_seconds() > _ttl_seconds()


def refresh_match_data():
    matches = scrape_matches()
    data = {
        "metadata": {
            "source_url": SOURCE_URL,
            "refreshed_at": _now_iso(),
            "match_count": len(matches),
            "display_timezone": os.getenv("WORLD_CUP_DISPLAY_TIMEZONE", "Europe/Dublin"),
        },
        "matches": matches,
    }
    _write_cache(data)
    return data


def get_match_data(force_refresh=False):
    cached = _read_cache()
    should_refresh = force_refresh or cached is None or _is_stale(cached)

    if should_refresh:
        try:
            return refresh_match_data()
        except Exception as exc:
            if cached:
                cached["error"] = f"Showing cached data; refresh failed: {exc}"
                return cached
            return {
                "metadata": {
                    "source_url": SOURCE_URL,
                    "refreshed_at": None,
                    "match_count": 0,
                },
                "matches": [],
                "error": f"Could not load match data: {exc}",
            }

    return cached
