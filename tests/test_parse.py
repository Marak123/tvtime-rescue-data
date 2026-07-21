"""Smoke test for the DioCache.db parser.

Builds a tiny fake DioCache.db with invented data (no real backup involved),
then checks that movies, series, watch history and the profile are extracted.

Run with:  python -m pytest    or    python tests/test_parse.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tvtime_rescue.extract.parse import parse_library  # noqa: E402


def _make_fake_diocache(path: Path) -> None:
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE cache_dio (key text, subKey text, max_age_date integer, "
        "max_stale_date integer, content BLOB, statusCode integer, headers BLOB, "
        "PRIMARY KEY (key, subKey))"
    )
    responses = [
        # A movie library response.
        {"status": "success", "data": {"type": "list", "objects": [{
            "uuid": "m1", "entity_type": "movie", "rewatch_count": 1,
            "watched_at": "2026-06-01T10:00:00Z", "filter": ["watched"],
            "extended": {"is_watched": True, "rating": 8},
            "meta": {"uuid": "m1", "name": "Fake Movie", "first_release_date": "2020-05-01",
                     "genres": ["Action"], "imdb_id": "tt0000001", "runtime": 6000,
                     "overview": "An invented movie for testing.",
                     "posters": [{"type": "poster", "url": "https://example.invalid/p.jpg"}]}}]}},
        # A series progress response.
        {"shows": [{
            "id": 12345, "name": "Fake Series", "watched_episode_count": 20,
            "aired_episode_count": 24, "status": "Continuing", "is_favorite": True,
            "is_archived": False, "is_for_later": False,
            "poster": {"url": "https://example.invalid/s.jpg"},
            "sorting": [{"id": "last_watched", "value": "1780000000"}]}], "id": 1, "name": "shows"},
        # A watch event response.
        {"status": "success", "data": {"type": "watch", "objects": [{
            "uuid": "m1", "entity_type": "movie", "runtime": 6000,
            "watched_at": "2026-06-01T10:00:00Z", "created_at": "2026-06-01T10:00:00Z"}]}},
        # A profile response.
        {"status": "success", "data": {
            "id": 999, "name": "TestUser", "is_vip": False, "is_premium": True}},
        # An episode list (top-level list) with per-episode watched status.
        [
            {"id": 5001, "name": "Pilot", "number": 1, "season_number": 1,
             "seen": True, "seen_date": "2026-01-02 20:00:00", "nb_times_watched": 2,
             "show": {"id": 12345, "name": "Fake Series"}},
            {"id": 5002, "name": "Second", "number": 2, "season_number": 1,
             "seen": False, "seen_date": "", "nb_times_watched": 0,
             "show": {"id": 12345, "name": "Fake Series"}},
        ],
    ]
    for i, r in enumerate(responses):
        con.execute("INSERT INTO cache_dio VALUES (?,?,?,?,?,?,?)",
                    (f"k{i}", "s", 0, 0, json.dumps(r).encode(), 200, b"{}"))
    con.commit()
    con.close()


def test_parse_library():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "DioCache.db"
        _make_fake_diocache(db)
        lib = parse_library(db)

    assert lib["stats"]["movies"] == 1
    assert lib["stats"]["series"] == 1
    assert lib["stats"]["episodes"] == 20
    assert lib["stats"]["favorites"] == 1
    assert lib["stats"]["watch_events"] == 1

    movie = lib["movies"][0]
    assert movie["title"] == "Fake Movie"
    assert movie["watched"] is True
    assert movie["year"] == "2020"
    assert movie["poster"].startswith("https://")

    series = lib["series"][0]
    assert series["title"] == "Fake Series"
    assert series["watched_eps"] == 20 and series["aired_eps"] == 24

    # Episode-level detail
    assert lib["stats"]["episode_details"] == 2
    assert lib["stats"]["episode_details_seen"] == 1
    assert len(series["episodes"]) == 2
    pilot = next(e for e in series["episodes"] if e["number"] == 1)
    assert pilot["seen"] is True and pilot["times_watched"] == 2

    assert lib["profile"]["name"] == "TestUser"
    print("OK - parser smoke test passed")


if __name__ == "__main__":
    test_parse_library()
