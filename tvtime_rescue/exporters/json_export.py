"""Universal JSON exporter.

Writes a single, cleanly named JSON file that anyone can build their own importer
against. This is the internal library.json tidied into a stable, documented
schema: clear field names, movies and series separated, and the full episode
list per series where available.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .base import format_imdb

SCHEMA_VERSION = 1

_README = """# Universal JSON export

tvtime_library.json is a clean, self-describing snapshot of everything recovered,
meant for building your own importer or feeding another tool.

Top level:
- schema_version, generated_at, source
- profile: { name, id }
- stats: counts
- movies: [ { title, year, imdb_id, watched, on_watchlist, watched_date,
             watched_at, rating (0-10 or null), rewatch_count, runtime_minutes,
             genres[], overview } ]
- series: [ { title, tvdb_id, year, status ("ended"/"running"), state
             ("watching"/"completed"/"stopped"/"plan"/...), watched_episodes,
             aired_episodes, favorite, archived, on_watchlist, last_watched,
             overview, genres[], episodes[] } ]
  where each episode is { season, number, name, watched (true/false/null),
             watched_date, times_watched, air_date }.

"watched" on an episode is null when the backup had no status for it (only known
around your current progress, unless the library was enriched from TheTVDB).
"""


def _series_state(s: dict) -> str:
    aired = int(s.get("aired_eps") or 0)
    watched = int(s.get("watched_eps") or 0)
    if s.get("for_later"):
        return "plan"
    if aired > 0 and watched >= aired:
        return "completed"
    if str(s.get("progress") or "") == "stopped":
        return "stopped"
    if watched > 0:
        return "watching"
    return "plan"


def _movie(m: dict) -> dict:
    return {
        "title": m.get("title", ""),
        "year": m.get("year", ""),
        "imdb_id": format_imdb(m.get("imdb_id")),
        "watched": bool(m.get("watched")),
        "on_watchlist": bool(m.get("watch_later")),
        "watched_date": m.get("watchedDate", ""),
        "watched_at": m.get("watched_at", ""),
        "rating": m["rating"] if (m.get("rating") or 0) > 0 else None,
        "rewatch_count": m.get("rewatch_count", 0) or 0,
        "runtime_minutes": m.get("runtime_min", "") or None,
        "genres": m.get("genres", []) or [],
        "overview": m.get("overview", ""),
    }


def _series(s: dict) -> dict:
    episodes = [{
        "season": e.get("season"),
        "number": e.get("number"),
        "name": e.get("name", ""),
        "watched": e.get("seen"),
        "watched_date": e.get("seen_date", ""),
        "times_watched": e.get("times_watched", 0) or 0,
        "air_date": e.get("air_date", ""),
    } for e in (s.get("episodes") or [])]
    return {
        "title": s.get("title", ""),
        "tvdb_id": s.get("id"),
        "year": s.get("year", ""),
        "status": "ended" if s.get("status") == "Ended" else "running",
        "state": _series_state(s),
        "watched_episodes": s.get("watched_eps", 0),
        "aired_episodes": s.get("aired_eps", 0),
        "favorite": bool(s.get("favorite")),
        "archived": bool(s.get("archived")),
        "on_watchlist": bool(s.get("for_later")),
        "last_watched": s.get("watchedDate", ""),
        "overview": s.get("overview", ""),
        "genres": s.get("genres", []) or [],
        "episodes": episodes,
    }


def export_json(lib: dict, out_dir: Path, log=print) -> dict:
    d = Path(out_dir) / "json"
    d.mkdir(parents=True, exist_ok=True)

    profile = lib.get("profile", {})
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "TV Time local backup (DioCache.db)",
        "profile": {"name": profile.get("name", ""), "id": profile.get("id", "")},
        "stats": lib.get("stats", {}),
        "movies": [_movie(m) for m in lib.get("movies", [])],
        "series": [_series(s) for s in lib.get("series", [])],
    }
    (d / "tvtime_library.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    (d / "README.md").write_text(_README, encoding="utf-8")

    log(f"  Universal JSON: {len(payload['movies'])} movies, {len(payload['series'])} series -> {d}")
    return {"movies": len(payload["movies"]), "series": len(payload["series"])}
