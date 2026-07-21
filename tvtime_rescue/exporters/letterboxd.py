"""Letterboxd exporter.

Letterboxd tracks films only, so this exports your movies: a diary CSV of
watched films (with dates, ratings and rewatch flags) and a separate watchlist
CSV. Import them at https://letterboxd.com/import/ (diary) and on your
watchlist page. Matching is by IMDb id, falling back to title and year.
"""
from __future__ import annotations

from pathlib import Path

from .base import format_imdb, stars_5, write_csv

_DIARY_FIELDS = ["Title", "Year", "imdbID", "WatchedDate", "Rating", "Rewatch", "Tags", "Review"]
_WATCHLIST_FIELDS = ["Title", "Year", "imdbID"]

_README = """# Letterboxd import

Letterboxd is for films only, so only your movies are here.

Files:
- letterboxd_diary.csv    - watched films with dates, ratings and rewatch flags
- letterboxd_watchlist.csv - films you had on your watchlist

How to import:
1. Go to https://letterboxd.com/import/
2. Upload letterboxd_diary.csv and follow the matching steps.
3. For the watchlist, open your Watchlist page on Letterboxd and use its import
   option with letterboxd_watchlist.csv (or import the diary first and add the
   rest by hand if you prefer).

Notes:
- Matching is by IMDb id first, then title and year.
- Ratings are converted from TV Time's 0-10 to Letterboxd's 0.5-5 stars.
"""


def export_letterboxd(lib: dict, out_dir: Path, log=print) -> dict:
    d = Path(out_dir) / "letterboxd"
    d.mkdir(parents=True, exist_ok=True)

    diary, watchlist = [], []
    for m in lib.get("movies", []):
        imdb = format_imdb(m.get("imdb_id"))
        if m.get("watched"):
            row = {"Title": m.get("title", ""), "Year": m.get("year", ""), "imdbID": imdb,
                   "WatchedDate": m.get("watchedDate", ""), "Tags": "tvtime"}
            if (m.get("rating") or 0) > 0:
                row["Rating"] = stars_5(m["rating"])
            if (m.get("rewatch_count") or 0) > 0:
                row["Rewatch"] = "Yes"
            diary.append(row)
        if m.get("watch_later"):
            watchlist.append({"Title": m.get("title", ""), "Year": m.get("year", ""), "imdbID": imdb})

    write_csv(d / "letterboxd_diary.csv", diary, _DIARY_FIELDS)
    write_csv(d / "letterboxd_watchlist.csv", watchlist, _WATCHLIST_FIELDS)
    (d / "README.md").write_text(_README, encoding="utf-8")

    log(f"  Letterboxd: {len(diary)} watched films, {len(watchlist)} on watchlist -> {d}")
    return {"diary": len(diary), "watchlist": len(watchlist)}
