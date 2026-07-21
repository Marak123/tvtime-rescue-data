"""Trakt.tv exporter.

Trakt tracks movies, shows and individual episodes. This writes a sync-API JSON
payload (the most complete form) plus simple per-list CSV files, so you can use
either Trakt's own importer (it accepts CSV and JSON) or a community tool such as
xbgmsharp/trakt.

Movies transfer fully (id, watched date, rating). For series, Trakt wants exact
episodes, but TV Time only stored per-series counts plus the handful of episodes
around your current progress. So shows are added to your watchlist and the
episodes the backup actually recorded are marked watched. For full series
progress, Simkl is the better target (see the simkl folder).
"""
from __future__ import annotations

import json
from pathlib import Path

from .base import format_imdb, iso_datetime, write_csv

_README = """# Trakt.tv import

Files:
- trakt_sync.json            - everything in Trakt's sync-API shape
- trakt_movies_history.csv   - watched movies (imdb, title, year, watched_at)
- trakt_movies_watchlist.csv - movies on your watchlist
- trakt_movies_ratings.csv   - your movie ratings
- trakt_shows_watchlist.csv  - series to add (tvdb, title, year)
- trakt_episodes_history.csv - the individual episodes the backup recorded

How to import (pick one):
- Trakt's own importer accepts CSV and JSON. Start at https://trakt.tv/ and look
  for the import option, then upload trakt_sync.json (or the CSV files).
- Or use the community tool xbgmsharp/trakt (github.com/xbgmsharp/trakt), which
  reads the CSV files here (one id per row) into history, watchlist or ratings.

Important about series: TV Time stored how many episodes of each show you
watched, not the full list, so Trakt cannot receive your exact episode history
from the backup alone. Shows are added to your watchlist and only the episodes
the backup explicitly recorded are marked watched. If you want complete series
progress, import the Simkl file instead - Simkl uses the same count-based model
TV Time did.
"""


def _movie_ids(m: dict) -> dict:
    imdb = format_imdb(m.get("imdb_id"))
    return {"imdb": imdb} if imdb else {}


def export_trakt(lib: dict, out_dir: Path, log=print) -> dict:
    d = Path(out_dir) / "trakt"
    d.mkdir(parents=True, exist_ok=True)

    hist_movies, watch_movies, rating_movies = [], [], []
    mv_hist_csv, mv_watch_csv, mv_rate_csv = [], [], []
    for m in lib.get("movies", []):
        ids = _movie_ids(m)
        entry = {"title": m.get("title", ""), "year": m.get("year", "")}
        if ids:
            entry["ids"] = ids
        if m.get("watched"):
            wm = dict(entry)
            if m.get("watched_at"):
                wm["watched_at"] = iso_datetime(m["watched_at"])
            hist_movies.append(wm)
            mv_hist_csv.append({"imdb": ids.get("imdb", ""), "title": m.get("title", ""),
                                "year": m.get("year", ""), "watched_at": iso_datetime(m.get("watched_at", ""))})
        if m.get("watch_later"):
            watch_movies.append(entry)
            mv_watch_csv.append({"imdb": ids.get("imdb", ""), "title": m.get("title", ""),
                                 "year": m.get("year", "")})
        if (m.get("rating") or 0) > 0:
            rating_movies.append({**entry, "rating": int(m["rating"])})
            mv_rate_csv.append({"imdb": ids.get("imdb", ""), "title": m.get("title", ""),
                                "year": m.get("year", ""), "rating": int(m["rating"])})

    # Series watchlist + known watched episodes
    series_by_id = {s.get("id"): s for s in lib.get("series", [])}
    watch_shows, shows_csv = [], []
    for s in lib.get("series", []):
        entry = {"title": s.get("title", ""), "year": s.get("year", "")}
        if s.get("id"):
            entry["ids"] = {"tvdb": s["id"]}
        if s.get("for_later") or s.get("watch_later"):
            watch_shows.append(entry)
        shows_csv.append({"tvdb": s.get("id", ""), "title": s.get("title", ""), "year": s.get("year", "")})

    # Known watched episodes -> grouped under shows/seasons for the history payload
    ep_csv = []
    grouped: dict = {}
    for e in lib.get("episodes", []):
        if e.get("seen") is not True:
            continue
        sid = e.get("show_id")
        if sid is None:
            continue
        season = e.get("season")
        number = e.get("number")
        watched_at = iso_datetime(e.get("seen_date", ""))
        grouped.setdefault(sid, {}).setdefault(season, []).append({"number": number, "watched_at": watched_at})
        ep_csv.append({"tvdb": sid, "season": season, "episode": number, "watched_at": watched_at})

    hist_shows = []
    for sid, seasons in grouped.items():
        s = series_by_id.get(sid, {})
        show = {"title": s.get("title", ""), "ids": {"tvdb": sid}, "seasons": []}
        for season_num, eps in sorted(seasons.items(), key=lambda kv: (kv[0] or 0)):
            show["seasons"].append({
                "number": season_num,
                "episodes": [ep for ep in {e["number"]: e for e in eps}.values()],
            })
        hist_shows.append(show)

    sync = {
        "history": {"movies": hist_movies, "shows": hist_shows},
        "watchlist": {"movies": watch_movies, "shows": watch_shows},
        "ratings": {"movies": rating_movies},
    }
    (d / "trakt_sync.json").write_text(json.dumps(sync, ensure_ascii=False, indent=1), encoding="utf-8")

    write_csv(d / "trakt_movies_history.csv", mv_hist_csv, ["imdb", "title", "year", "watched_at"])
    write_csv(d / "trakt_movies_watchlist.csv", mv_watch_csv, ["imdb", "title", "year"])
    write_csv(d / "trakt_movies_ratings.csv", mv_rate_csv, ["imdb", "title", "year", "rating"])
    write_csv(d / "trakt_shows_watchlist.csv", shows_csv, ["tvdb", "title", "year"])
    write_csv(d / "trakt_episodes_history.csv", ep_csv, ["tvdb", "season", "episode", "watched_at"])
    (d / "README.md").write_text(_README, encoding="utf-8")

    log(f"  Trakt: {len(hist_movies)} watched movies, {len(shows_csv)} shows, "
        f"{len(ep_csv)} known episodes -> {d}")
    return {"movies_history": len(hist_movies), "movies_watchlist": len(watch_movies),
            "shows": len(shows_csv), "episodes": len(ep_csv)}
