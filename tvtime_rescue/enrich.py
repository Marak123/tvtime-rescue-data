"""Optional enrichment from TheTVDB v4 API.

If a TVDB API key is available, this fills in the gaps the backup could not:
series descriptions and genres, and the full season/episode list for every
show. The real watched status recovered from the backup is overlaid on top, so
episodes you actually watched stay marked; episodes the backup never knew about
are marked as unknown rather than guessed.

The key is read from (in order): an explicit argument, the TVDB_API_KEY
environment variable, or a .env file. Nothing here runs unless a key is found.
Only the Python standard library is used (urllib), so no extra dependency and
nothing to bundle into the executable.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TVDB_BASE = "https://api4.thetvdb.com/v4"


# --------------------------------------------------------------------------
# Key loading
# --------------------------------------------------------------------------
def _parse_env_file(path: Path) -> dict:
    out: dict = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            out[key.strip()] = val.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def _env_candidates() -> list[Path]:
    here = [Path.cwd()]
    # next to a PyInstaller executable, or the project root when run from source
    try:
        here.append(Path(sys.argv[0]).resolve().parent)
    except Exception:
        pass
    here.append(Path(__file__).resolve().parent.parent)
    seen, out = set(), []
    for p in here:
        if p not in seen:
            seen.add(p)
            out.append(p / ".env")
    return out


def load_key(explicit: str | None = None) -> tuple[str | None, str | None]:
    """Return (api_key, pin). Looks at the argument, then env vars, then .env."""
    key = (explicit or "").strip() or os.environ.get("TVDB_API_KEY", "").strip()
    pin = os.environ.get("TVDB_PIN", "").strip()
    if not key:
        for env_file in _env_candidates():
            if env_file.is_file():
                values = _parse_env_file(env_file)
                key = (values.get("TVDB_API_KEY") or "").strip()
                pin = pin or (values.get("TVDB_PIN") or "").strip()
                if key:
                    break
    return (key or None), (pin or None)


# --------------------------------------------------------------------------
# TVDB client (stdlib only)
# --------------------------------------------------------------------------
class TVDBClient:
    def __init__(self, api_key: str, pin: str | None = None,
                 cache_dir: Path | None = None, log=print):
        self.api_key = api_key
        self.pin = pin
        self.cache_dir = cache_dir
        self.log = log
        self.token: str | None = None
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def _call(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(TVDB_BASE + path, data=data, method=method)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        last_err = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    last_err = exc
                    continue
                raise
            except urllib.error.URLError as exc:
                last_err = exc
                time.sleep(1.0 * (attempt + 1))
        raise last_err  # type: ignore[misc]

    def login(self) -> None:
        body = {"apikey": self.api_key}
        if self.pin:
            body["pin"] = self.pin
        resp = self._call("POST", "/login", body)
        self.token = (resp.get("data") or {}).get("token")
        if not self.token:
            raise RuntimeError("TVDB login did not return a token. Check the API key.")

    def _get_cached(self, path: str, cache_name: str):
        if self.cache_dir:
            cf = self.cache_dir / cache_name
            if cf.is_file():
                try:
                    return json.loads(cf.read_text(encoding="utf-8"))
                except Exception:
                    pass
        resp = self._call("GET", path)
        if self.cache_dir:
            try:
                (self.cache_dir / cache_name).write_text(
                    json.dumps(resp, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
        time.sleep(0.05)  # be polite to the API
        return resp

    def series_extended(self, series_id) -> dict:
        resp = self._get_cached(f"/series/{series_id}/extended?short=true",
                                f"series_{series_id}_ext.json")
        return resp.get("data") or {}

    def series_episodes(self, series_id) -> list:
        episodes, page, guard = [], 0, 0
        while guard < 60:
            guard += 1
            resp = self._get_cached(
                f"/series/{series_id}/episodes/default?page={page}",
                f"series_{series_id}_eps_{page}.json")
            data = resp.get("data") or {}
            batch = data.get("episodes") or []
            episodes.extend(batch)
            nxt = (resp.get("links") or {}).get("next")
            if not batch or not nxt:
                break
            page += 1
        return episodes


def make_client(api_key: str, pin: str | None, cache_dir: Path | None, log=print) -> TVDBClient:
    return TVDBClient(api_key, pin, cache_dir, log)


# --------------------------------------------------------------------------
# Enrichment
# --------------------------------------------------------------------------
def _watched_overlays(lib: dict):
    """Maps from the backup's real per-episode watched status."""
    by_ep_id, by_sn = {}, {}
    for e in lib.get("episodes", []):
        info = {"seen": bool(e["seen"]), "seen_date": e.get("seen_date", ""),
                "times": e.get("times_watched", 0) or 0}
        if e.get("episode_id") is not None:
            by_ep_id[e["episode_id"]] = info
        by_sn[(e.get("show_id"), e.get("season"), e.get("number"))] = info
    return by_ep_id, by_sn


def enrich_library(lib: dict, client: TVDBClient, *, fetch_episodes: bool = True,
                   log=print) -> dict:
    """Fill series overview/genres and full episode lists using a TVDB client."""
    by_ep_id, by_sn = _watched_overlays(lib)
    series = lib["series"]
    total = len(series)
    enriched_desc = enriched_eps = 0

    for i, s in enumerate(series, 1):
        sid = s.get("id")
        if not sid:
            continue
        try:
            ext = client.series_extended(sid)
        except Exception as exc:
            log(f"    [{i}/{total}] {s['title']}: could not fetch details ({type(exc).__name__})")
            ext = {}
        if ext:
            if not s.get("overview"):
                s["overview"] = ext.get("overview") or ""
            if not s.get("genres"):
                s["genres"] = [g.get("name") for g in (ext.get("genres") or []) if g.get("name")]
            if not s.get("year") and ext.get("year"):
                s["year"] = str(ext["year"])
            if s.get("overview"):
                enriched_desc += 1

        if fetch_episodes:
            try:
                raw = client.series_episodes(sid)
            except Exception as exc:
                log(f"    [{i}/{total}] {s['title']}: could not fetch episodes ({type(exc).__name__})")
                raw = []
            full = []
            for ep in raw:
                sn, num = ep.get("seasonNumber"), ep.get("number")
                ov = by_ep_id.get(ep.get("id")) or by_sn.get((sid, sn, num))
                if ov is None:
                    seen, seen_date, times = None, "", 0
                else:
                    seen, seen_date, times = ov["seen"], ov["seen_date"], ov["times"]
                full.append({
                    "season": sn, "number": num, "name": ep.get("name") or "",
                    "air_date": ep.get("aired") or "",
                    "seen": seen, "seen_date": seen_date, "times_watched": times,
                })
            if full:
                full.sort(key=lambda e: (e["season"] if e["season"] is not None else 999,
                                         e["number"] or 0))
                s["episodes"] = full
                s["episodes_full"] = True
                enriched_eps += 1

        if i % 10 == 0 or i == total:
            log(f"    {i}/{total} series processed")

    lib.setdefault("stats", {})
    lib["stats"]["tvdb_enriched_descriptions"] = enriched_desc
    lib["stats"]["tvdb_enriched_episode_lists"] = enriched_eps
    log(f"  TVDB enrichment done: {enriched_desc} descriptions, {enriched_eps} full episode lists.")
    return lib
