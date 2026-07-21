"""Shared helpers for the platform exporters."""
from __future__ import annotations

import csv
import json
from pathlib import Path


def save_library(lib: dict, path: Path) -> None:
    path.write_text(json.dumps(lib, ensure_ascii=False), encoding="utf-8")


def load_library(input_dir) -> dict:
    """Load library.json from a recovered-output folder (or a direct file path)."""
    p = Path(input_dir).expanduser()
    lib_file = p if p.suffix == ".json" else p / "library.json"
    if not lib_file.is_file():
        raise FileNotFoundError(
            f"Could not find library.json at '{lib_file}'.\n"
            "Run the recover step first, then point the exporter at that output folder."
        )
    return json.loads(lib_file.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def format_imdb(raw) -> str:
    """Normalise an IMDb id to tt + at least 7 digits (what Simkl/Letterboxd expect)."""
    if not raw:
        return ""
    s = str(raw).strip()
    num = s[2:] if s.lower().startswith("tt") else s
    if not num.isdigit():
        return ""
    return "tt" + num.zfill(7)


def stars_5(rating10) -> str:
    """Convert a 0-10 rating to Letterboxd's 0.5-5 star scale."""
    try:
        r = float(rating10)
    except (TypeError, ValueError):
        return ""
    if r <= 0:
        return ""
    stars = round(r) / 2
    return str(int(stars)) if stars.is_integer() else str(stars)


def iso_datetime(value: str) -> str:
    """Normalise a date/datetime string to an ISO-8601 UTC stamp for Trakt."""
    if not value:
        return ""
    v = value.strip()
    if "T" in v:
        return v if v.endswith("Z") else v + "Z"
    if " " in v:  # "2026-05-26 17:31:19"
        return v.replace(" ", "T") + "Z"
    if len(v) == 10:  # date only
        return v + "T00:00:00Z"
    return v


def last_watched_episode(series: dict) -> str:
    """Best available 'last watched episode' as sXXeYY, for Simkl progress.

    If the full aired episode list is present (TVDB enrichment), the watched
    count maps to the Nth aired episode - the same sequential model Simkl uses.
    Otherwise fall back to the latest episode the backup explicitly marked seen.
    """
    eps = series.get("episodes") or []
    aired = sorted((e for e in eps if (e.get("season") or 0) > 0),
                   key=lambda e: (e.get("season") or 0, e.get("number") or 0))
    watched = int(series.get("watched_eps") or 0)
    if series.get("episodes_full") and aired and watched > 0:
        pick = aired[min(watched, len(aired)) - 1]
        return f"s{int(pick['season']):02d}e{int(pick['number']):02d}"
    seen = [e for e in aired if e.get("seen") is True]
    if seen:
        pick = max(seen, key=lambda e: (e.get("season") or 0, e.get("number") or 0))
        return f"s{int(pick['season']):02d}e{int(pick['number']):02d}"
    return ""


def run_exports(lib: dict, out_dir: Path,
                platforms=("letterboxd", "simkl", "trakt", "imdb", "json"),
                log=print) -> dict:
    """Run the requested exporters. Imported lazily to avoid circular imports."""
    from .imdb import export_imdb
    from .json_export import export_json
    from .letterboxd import export_letterboxd
    from .simkl import export_simkl
    from .trakt import export_trakt

    funcs = {"letterboxd": export_letterboxd, "simkl": export_simkl, "trakt": export_trakt,
             "imdb": export_imdb, "json": export_json}
    results = {}
    for name in platforms:
        fn = funcs.get(name)
        if fn is None:
            continue
        results[name] = fn(lib, out_dir, log=log)
    return results
