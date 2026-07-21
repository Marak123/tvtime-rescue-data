"""Simkl exporter.

Simkl fits TV Time best: it tracks movies and series, with a per-series status
and a "last episode watched" that maps directly onto TV Time's episode counts.
Produces one CSV in Simkl's documented import format. Import it at
https://simkl.com/apps/import/csv/
"""
from __future__ import annotations

from pathlib import Path

from .base import format_imdb, last_watched_episode, write_csv

_FIELDS = ["SIMKL_ID", "Title", "Type", "Year", "Watchlist", "LastEpWatched",
           "WatchedDate", "Rating", "Memo", "TVDB", "TMDB", "IMDB"]

_README = """# Simkl import

Simkl tracks both movies and series, so everything is in one file:
simkl_import.csv

How to import:
1. Go to https://simkl.com/apps/import/csv/
2. Upload simkl_import.csv.

How TV Time maps to Simkl:
- Movies you watched  -> completed
- Movies on your list -> plantowatch
- Series fully watched -> completed
- Series in progress   -> watching, with LastEpWatched set from your episode count
- Series you stopped   -> hold
- Series for later     -> plantowatch

Note on episodes: TV Time stored how many episodes of each series you watched,
not the exact list. Simkl uses the same "watched up to episode X" model, so the
LastEpWatched column is set to the Nth aired episode. This is most accurate when
the library was enriched with a TheTVDB key (full episode lists); otherwise it
uses the latest episode the backup explicitly recorded.
"""


def _movie_status(m: dict) -> str:
    if m.get("watched"):
        return "completed"
    if m.get("watch_later"):
        return "plantowatch"
    return ""


def _series_status(s: dict) -> str:
    aired = int(s.get("aired_eps") or 0)
    watched = int(s.get("watched_eps") or 0)
    if s.get("for_later"):
        return "plantowatch"
    if aired > 0 and watched >= aired:
        return "completed"
    if str(s.get("progress") or "") == "stopped":
        return "hold"
    if watched > 0:
        return "watching"
    return "plantowatch"


def export_simkl(lib: dict, out_dir: Path, log=print) -> dict:
    d = Path(out_dir) / "simkl"
    d.mkdir(parents=True, exist_ok=True)

    rows = []
    n_movies = n_series = 0
    for m in lib.get("movies", []):
        status = _movie_status(m)
        if not status:
            continue
        rows.append({
            "SIMKL_ID": "", "Title": m.get("title", ""), "Type": "movie",
            "Year": m.get("year", ""), "Watchlist": status, "LastEpWatched": "",
            "WatchedDate": m.get("watchedDate", ""),
            "Rating": m["rating"] if (m.get("rating") or 0) > 0 else "",
            "Memo": "", "TVDB": "", "TMDB": "", "IMDB": format_imdb(m.get("imdb_id")),
        })
        n_movies += 1
    for s in lib.get("series", []):
        rows.append({
            "SIMKL_ID": "", "Title": s.get("title", ""), "Type": "tv",
            "Year": s.get("year", ""), "Watchlist": _series_status(s),
            "LastEpWatched": last_watched_episode(s),
            "WatchedDate": s.get("watchedDate", ""), "Rating": "", "Memo": "",
            "TVDB": s.get("id", ""), "TMDB": "", "IMDB": "",
        })
        n_series += 1

    write_csv(d / "simkl_import.csv", rows, _FIELDS)
    (d / "README.md").write_text(_README, encoding="utf-8")

    log(f"  Simkl: {n_movies} movies, {n_series} series -> {d}")
    return {"movies": n_movies, "series": n_series}
