"""IMDb exporter.

IMDb tracks ratings and a watchlist (not a separate "watched" list), so this
writes CSVs in IMDb's own export layout: your ratings and your watchlist. Films
only, since the series in the backup do not carry IMDb ids.

These files double as a universal "IMDb CSV", which Letterboxd, Simkl and Trakt
all accept as an import source, so they are handy even beyond IMDb itself.
"""
from __future__ import annotations

from pathlib import Path

from .base import format_imdb, write_csv

_RATING_FIELDS = ["Const", "Your Rating", "Date Rated", "Title", "Title Type",
                  "IMDb Rating", "Runtime (mins)", "Year", "Genres", "URL"]
_WATCHLIST_FIELDS = ["Const", "Title", "Title Type", "Year", "Genres", "URL"]

_README = """# IMDb import

IMDb only models ratings and a watchlist (there is no plain "watched" list), and
the series in the backup have no IMDb ids, so this is films only:

- imdb_ratings.csv   - films you rated (Const, Your Rating, Date Rated, ...)
- imdb_watchlist.csv - films on your watchlist

IMDb itself no longer offers a general CSV import, but these files are in the
standard "IMDb CSV" layout, which Letterboxd, Simkl and Trakt all accept as an
import source. For your full watched history, the Letterboxd or Simkl files are
the better choice.
"""


def _url(imdb: str) -> str:
    return f"https://www.imdb.com/title/{imdb}/" if imdb else ""


def export_imdb(lib: dict, out_dir: Path, log=print) -> dict:
    d = Path(out_dir) / "imdb"
    d.mkdir(parents=True, exist_ok=True)

    ratings, watchlist = [], []
    for m in lib.get("movies", []):
        imdb = format_imdb(m.get("imdb_id"))
        genres = ", ".join(m.get("genres", []) or [])
        if (m.get("rating") or 0) > 0:
            ratings.append({
                "Const": imdb, "Your Rating": int(m["rating"]),
                "Date Rated": m.get("watchedDate", ""), "Title": m.get("title", ""),
                "Title Type": "Movie", "IMDb Rating": "",
                "Runtime (mins)": m.get("runtime_min", "") or "",
                "Year": m.get("year", ""), "Genres": genres, "URL": _url(imdb),
            })
        if m.get("watch_later"):
            watchlist.append({
                "Const": imdb, "Title": m.get("title", ""), "Title Type": "Movie",
                "Year": m.get("year", ""), "Genres": genres, "URL": _url(imdb),
            })

    write_csv(d / "imdb_ratings.csv", ratings, _RATING_FIELDS)
    write_csv(d / "imdb_watchlist.csv", watchlist, _WATCHLIST_FIELDS)
    (d / "README.md").write_text(_README, encoding="utf-8")

    log(f"  IMDb: {len(ratings)} rated films, {len(watchlist)} on watchlist -> {d}")
    return {"ratings": len(ratings), "watchlist": len(watchlist)}
