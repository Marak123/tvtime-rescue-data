"""Tests for the platform exporters (no network)."""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tvtime_rescue.exporters import base, run_exports  # noqa: E402


def _sample_lib() -> dict:
    return {
        "movies": [
            {"title": "Good Movie", "year": "2020", "imdb_id": "tt1234567", "watched": True,
             "watch_later": False, "watched_at": "2026-06-01T10:00:00Z", "watchedDate": "2026-06-01",
             "rewatch_count": 2, "rating": 8, "genres": ["Action"]},
            {"title": "Later Movie", "year": "2019", "imdb_id": "tt7654321", "watched": False,
             "watch_later": True, "watched_at": "", "watchedDate": "", "rewatch_count": 0, "rating": 0},
        ],
        "series": [
            {"id": 72108, "title": "Long Show", "year": "2003", "watched_eps": 2, "aired_eps": 3,
             "status": "Continuing", "progress": "watching", "favorite": False, "archived": False,
             "for_later": False, "watchedDate": "2026-07-01", "episodes_full": True, "episodes": [
                 {"season": 1, "number": 1, "name": "A", "seen": True, "seen_date": "2026-05-01 20:00:00", "times_watched": 1, "show_id": 72108},
                 {"season": 1, "number": 2, "name": "B", "seen": True, "seen_date": "2026-05-02 20:00:00", "times_watched": 1, "show_id": 72108},
                 {"season": 1, "number": 3, "name": "C", "seen": None, "seen_date": "", "times_watched": 0, "show_id": 72108},
             ]},
        ],
        "episodes": [
            {"episode_id": 900, "show_id": 72108, "season": 1, "number": 1, "seen": True,
             "seen_date": "2026-05-01 20:00:00", "times_watched": 1},
            {"episode_id": 901, "show_id": 72108, "season": 1, "number": 2, "seen": True,
             "seen_date": "2026-05-02 20:00:00", "times_watched": 1},
        ],
        "profile": {"name": "Tester"},
        "stats": {"movies": 2, "series": 1, "episodes": 2},
    }


def _read_csv(path: Path):
    with path.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def test_helpers():
    assert base.format_imdb("tt123") == "tt0000123"
    assert base.format_imdb("456") == "tt0000456"
    assert base.stars_5(8) == "4"
    assert base.stars_5(7) == "3.5"
    assert base.iso_datetime("2026-05-01 20:00:00") == "2026-05-01T20:00:00Z"
    print("OK - exporter helpers")


def test_run_all_exports():
    lib = _sample_lib()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        run_exports(lib, out, log=lambda *_: None)

        # Letterboxd (movies only)
        diary = _read_csv(out / "letterboxd" / "letterboxd_diary.csv")
        assert len(diary) == 1 and diary[0]["imdbID"] == "tt1234567"
        assert diary[0]["Rating"] == "4" and diary[0]["Rewatch"] == "Yes"
        wl = _read_csv(out / "letterboxd" / "letterboxd_watchlist.csv")
        assert len(wl) == 1 and wl[0]["Title"] == "Later Movie"

        # Simkl (movies + series with LastEpWatched from the count)
        simkl = _read_csv(out / "simkl" / "simkl_import.csv")
        movie = next(r for r in simkl if r["Type"] == "movie" and r["Title"] == "Good Movie")
        assert movie["Watchlist"] == "completed" and movie["IMDB"] == "tt1234567"
        show = next(r for r in simkl if r["Type"] == "tv")
        assert show["TVDB"] == "72108" and show["Watchlist"] == "watching"
        assert show["LastEpWatched"] == "s01e02"   # 2nd aired episode of the count

        # Trakt (episodes history for the known watched episodes)
        eps = _read_csv(out / "trakt" / "trakt_episodes_history.csv")
        assert len(eps) == 2 and eps[0]["tvdb"] == "72108"
        hist = _read_csv(out / "trakt" / "trakt_movies_history.csv")
        assert any(r["imdb"] == "tt1234567" for r in hist)

        # IMDb (ratings + watchlist, films only)
        imdb_r = _read_csv(out / "imdb" / "imdb_ratings.csv")
        assert len(imdb_r) == 1 and imdb_r[0]["Const"] == "tt1234567"
        assert imdb_r[0]["Your Rating"] == "8"
        imdb_w = _read_csv(out / "imdb" / "imdb_watchlist.csv")
        assert len(imdb_w) == 1 and imdb_w[0]["Title"] == "Later Movie"

        # Universal JSON (clean schema, unknown episode status preserved as null)
        import json as _json
        uni = _json.loads((out / "json" / "tvtime_library.json").read_text(encoding="utf-8"))
        assert uni["schema_version"] == 1
        assert len(uni["movies"]) == 2 and len(uni["series"]) == 1
        s0 = uni["series"][0]
        assert s0["tvdb_id"] == 72108 and s0["state"] == "watching"
        assert s0["episodes"][2]["watched"] is None
    print("OK - all exporters produced correct files")


if __name__ == "__main__":
    test_helpers()
    test_run_all_exports()
