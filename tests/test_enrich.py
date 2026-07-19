"""Tests for the optional TVDB enrichment (no network; a fake client is used)."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tvtime_rescue import enrich  # noqa: E402


class FakeClient:
    """Stand-in for TVDBClient so the overlay logic can be tested offline."""
    def login(self):
        pass

    def series_extended(self, sid):
        return {"overview": "An overview.", "genres": [{"name": "Drama"}, {"name": "Crime"}],
                "year": 2020}

    def series_episodes(self, sid):
        return [
            {"id": 900, "seasonNumber": 1, "number": 1, "name": "Pilot", "aired": "2020-01-01"},
            {"id": 901, "seasonNumber": 1, "number": 2, "name": "Second", "aired": "2020-01-08"},
            {"id": 902, "seasonNumber": 2, "number": 1, "name": "Return", "aired": "2021-01-01"},
        ]


def test_enrich_overlays_watched_status():
    lib = {
        "series": [{"id": 100, "title": "Test Show", "overview": "", "genres": [],
                    "year": "", "episodes": []}],
        "episodes": [{"episode_id": 900, "show_id": 100, "season": 1, "number": 1,
                      "seen": True, "seen_date": "2026-01-01", "times_watched": 1}],
        "stats": {},
    }
    enrich.enrich_library(lib, FakeClient(), log=lambda *_: None)
    s = lib["series"][0]

    assert s["overview"] == "An overview."
    assert s["genres"] == ["Drama", "Crime"]
    assert s.get("episodes_full") is True
    assert len(s["episodes"]) == 3

    e1 = next(e for e in s["episodes"] if e["season"] == 1 and e["number"] == 1)
    e2 = next(e for e in s["episodes"] if e["season"] == 1 and e["number"] == 2)
    assert e1["seen"] is True and e1["name"] == "Pilot"      # real watched status overlaid
    assert e2["seen"] is None                               # unknown, not guessed
    print("OK - enrichment overlay test passed")


def test_load_key_precedence():
    # explicit argument wins
    assert enrich.load_key("explicit-key")[0] == "explicit-key"

    # environment variable
    os.environ["TVDB_API_KEY"] = "env-key"
    try:
        assert enrich.load_key()[0] == "env-key"
    finally:
        del os.environ["TVDB_API_KEY"]

    # .env file parsing
    with tempfile.TemporaryDirectory() as tmp:
        env = Path(tmp) / ".env"
        env.write_text('TVDB_API_KEY="file-key"\nTVDB_PIN=1234\n', encoding="utf-8")
        values = enrich._parse_env_file(env)
        assert values["TVDB_API_KEY"] == "file-key"
        assert values["TVDB_PIN"] == "1234"
    print("OK - key loading test passed")


if __name__ == "__main__":
    test_enrich_overlays_watched_status()
    test_load_key_precedence()
