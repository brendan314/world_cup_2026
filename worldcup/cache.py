import json
import os
from datetime import datetime, timezone
from pathlib import Path

from worldcup.normalize import enrich_matches
from worldcup.scrape import SOURCE_URL, scrape_matches


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BUNDLED_CACHE_FILE = DATA_DIR / "matches.json"
DEFAULT_TTL_SECONDS = 60 * 60 * 3


def _runtime_cache_file():
    configured = os.getenv("WORLD_CUP_CACHE_FILE")
    if configured:
        return Path(configured)
    if os.getenv("VERCEL"):
        return Path("/tmp/try_world_cup/matches.json")
    return BUNDLED_CACHE_FILE


def _ttl_seconds():
    raw = os.getenv("WORLD_CUP_CACHE_TTL_SECONDS", str(DEFAULT_TTL_SECONDS))
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_TTL_SECONDS


def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_cache():
    for cache_file in (_runtime_cache_file(), BUNDLED_CACHE_FILE):
        if not cache_file.exists():
            continue
        with cache_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
            data["matches"] = enrich_matches(data.get("matches", []))
            return data
    return None


def _write_cache(data):
    cache_file = _runtime_cache_file()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with cache_file.open("w", encoding="utf-8") as file:
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
