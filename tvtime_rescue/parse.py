"""Parse DioCache.db (TV Time's local API response cache) into structured data.

DioCache.db is a Dio (Dart/Flutter HTTP client) cache: one table `cache_dio`
whose `content` column holds raw JSON API responses. TV Time is a Flutter app,
so its last-seen library, series progress and watch history sit here as plain
JSON. This module turns that into movies, series, watch events and a profile,
then writes CSV files and a Markdown report.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _iso_to_ms(s: str) -> int:
    if not s:
        return 0
    try:
        return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)
    except Exception:
        return 0


def _walk(obj):
    """Yield every dict found anywhere inside a nested JSON structure."""
    stack = [obj]
    while stack:
        x = stack.pop()
        if isinstance(x, dict):
            yield x
            stack.extend(x.values())
        elif isinstance(x, list):
            stack.extend(x)


def _first_image(meta: dict, kind: str) -> str:
    pools = []
    if kind == "poster":
        pools = [meta.get("posters"), meta.get("images")]
    else:
        pools = [meta.get("images"), meta.get("fanart")]
    for pool in pools:
        for it in (pool or []):
            if isinstance(it, dict) and it.get("type", kind) == kind and it.get("url"):
                return it["url"]
    # any image as a last resort
    for pool in pools:
        for it in (pool or []):
            if isinstance(it, dict) and it.get("url"):
                return it["url"]
    return ""


def load_cache(diocache: Path) -> list[tuple]:
    con = sqlite3.connect(f"file:{diocache.as_posix()}?mode=ro", uri=True)
    rows = con.execute("SELECT key, subKey, max_age_date, content FROM cache_dio").fetchall()
    con.close()
    out = []
    for key, subkey, max_age, content in rows:
        try:
            out.append((key, subkey, max_age or 0, json.loads(content)))
        except Exception:
            continue
    return out


def _build_movies(cache) -> list[dict]:
    movies: dict[str, dict] = {}
    for _k, _s, _age, d in cache:
        if not isinstance(d, dict):
            continue
        data = d.get("data")
        if not (isinstance(data, dict) and isinstance(data.get("objects"), list)):
            continue
        for o in data["objects"]:
            if not isinstance(o, dict) or o.get("entity_type") != "movie":
                continue
            meta = o.get("meta") or {}
            name = meta.get("name") or o.get("name")
            if not name:
                continue
            uid = meta.get("uuid") or meta.get("imdb_id") or o.get("uuid") or name
            ext = o.get("extended") or {}
            flt = [str(x) for x in (o.get("filter") or [])]
            rec = movies.get(uid)
            if rec is None:
                rec = {
                    "kind": "movie", "title": name, "year": "", "genres": [],
                    "overview": "", "poster": "", "fanart": "", "imdb_id": meta.get("imdb_id", ""),
                    "runtime_min": 0, "watched": False, "watch_later": False,
                    "watched_at": "", "rewatch_count": 0, "rating": 0, "_filters": set(),
                }
                movies[uid] = rec
            ov = (meta.get("overview") or "").strip()
            if len(ov) > len(rec["overview"]):
                rec["overview"] = ov
            if not rec["poster"]:
                rec["poster"] = _first_image(meta, "poster")
            if not rec["fanart"]:
                rec["fanart"] = _first_image(meta, "fanart")
            if meta.get("genres"):
                rec["genres"] = meta["genres"]
            if meta.get("runtime"):
                rec["runtime_min"] = round(meta["runtime"] / 60)
            if not rec["year"] and meta.get("first_release_date"):
                rec["year"] = str(meta["first_release_date"])[:4]
            rec["_filters"].update(flt)
            rec["watched"] = rec["watched"] or ("watched" in flt) or bool(ext.get("is_watched"))
            wa = o.get("watched_at") or ""
            if wa > rec["watched_at"]:
                rec["watched_at"] = wa
            rec["rewatch_count"] = max(rec["rewatch_count"], o.get("rewatch_count") or 0)
            rec["rating"] = max(rec["rating"], ext.get("rating") or 0)

    out = []
    for r in movies.values():
        flt = r.pop("_filters")
        r["watch_later"] = "watch_later" in flt
        r["watchedDate"] = r["watched_at"][:10]
        r["sortDate"] = _iso_to_ms(r["watched_at"])
        out.append(r)
    return out


def _build_series(cache) -> list[dict]:
    shows: dict[int, dict] = {}
    age: dict[int, int] = {}
    # Primary source: the "shows" progress endpoint (episode counts + posters).
    for _k, _s, max_age, d in cache:
        if not (isinstance(d, dict) and isinstance(d.get("shows"), list)):
            continue
        for s in d["shows"]:
            if not isinstance(s, dict) or "id" not in s:
                continue
            sid = s["id"]
            if sid in age and max_age <= age[sid]:
                continue
            age[sid] = max_age
            filters = {f.get("id"): f.get("values") for f in s.get("filters", []) if isinstance(f, dict)}
            sort = {x.get("id"): x.get("value") for x in s.get("sorting", []) if isinstance(x, dict)}
            lw = sort.get("last_watched")
            shows[sid] = {
                "kind": "series", "id": sid, "title": s.get("name", ""),
                "poster": (s.get("poster") or {}).get("url", ""),
                "fanart": (s.get("fanart") or {}).get("url", ""),
                "watched_eps": s.get("watched_episode_count") or 0,
                "aired_eps": s.get("aired_episode_count") or 0,
                "status": s.get("status", ""),
                "progress": ", ".join(filters.get("progress", []) or []),
                "favorite": bool(s.get("is_favorite")),
                "archived": bool(s.get("is_archived")),
                "for_later": bool(s.get("is_for_later")),
                "up_to_date": bool(s.get("is_up_to_date")),
                "overview": "", "genres": [], "year": "",
                "sortDate": int(lw) * 1000 if str(lw).isdigit() else 0,
            }
    # Enrich posters from the series list endpoint (matched by name).
    by_name = {v["title"].lower(): v for v in shows.values()}
    for _k, _s, _age, d in cache:
        if not isinstance(d, dict):
            continue
        data = d.get("data")
        if not (isinstance(data, dict) and isinstance(data.get("objects"), list)):
            continue
        for o in data["objects"]:
            if not isinstance(o, dict) or o.get("entity_type") != "series":
                continue
            meta = o.get("meta") or {}
            rec = by_name.get((meta.get("name") or "").lower())
            if rec is None:
                continue
            if not rec["poster"]:
                rec["poster"] = _first_image(meta, "poster")
            if not rec["fanart"]:
                rec["fanart"] = _first_image(meta, "fanart")

    for r in shows.values():
        r["watchedDate"] = (datetime.fromtimestamp(r["sortDate"] / 1000, timezone.utc)
                            .strftime("%Y-%m-%d") if r["sortDate"] else "")
    return sorted(shows.values(), key=lambda r: str(r["title"]).lower())


def _build_watch_events(cache) -> list[dict]:
    seen, out = set(), []
    for _k, _s, _age, d in cache:
        if not isinstance(d, dict):
            continue
        data = d.get("data")
        if not (isinstance(data, dict) and data.get("type") == "watch"):
            continue
        for o in data.get("objects", []):
            if not isinstance(o, dict):
                continue
            sig = (o.get("uuid"), o.get("watched_at"), o.get("entity_type"))
            if sig in seen:
                continue
            seen.add(sig)
            out.append({
                "entity_type": o.get("entity_type", ""),
                "watched_at": o.get("watched_at", ""),
                "created_at": o.get("created_at", ""),
                "runtime_min": round(o.get("runtime", 0) / 60) if o.get("runtime") else "",
                "uuid": o.get("uuid", ""),
            })
    out.sort(key=lambda r: str(r["watched_at"]), reverse=True)
    return out


def _build_episodes(cache) -> list[dict]:
    """Individual episodes TV Time cached around the user's current progress.

    This is NOT the full episode list of every show. The app only kept the
    episodes near your position (the up-next queue and recently watched), so
    coverage is partial. Each episode carries a real watched flag, so what is
    here is accurate; it is just not complete.
    """
    eps: dict = {}
    for _k, _s, _age, d in cache:
        for x in _walk(d):
            if "season_number" not in x or "number" not in x:
                continue
            if not ("seen" in x or "is_watched" in x or "seen_date" in x):
                continue
            eid = x.get("id")
            if eid is None:
                continue
            show = x.get("show") if isinstance(x.get("show"), dict) else {}
            seen = bool(x.get("seen") or x.get("is_watched"))
            nb = x.get("nb_times_watched") or 0
            seen_date = (x.get("seen_date") or "")[:19]
            rec = eps.get(eid)
            if rec is None:
                eps[eid] = {
                    "episode_id": eid,
                    "show_id": show.get("id"),
                    "show": show.get("name", ""),
                    "season": x.get("season_number"),
                    "number": x.get("number"),
                    "name": x.get("name", ""),
                    "seen": seen,
                    "seen_date": seen_date,
                    "times_watched": nb,
                    "air_date": x.get("air_date") or "",
                }
            else:
                rec["seen"] = rec["seen"] or seen
                rec["times_watched"] = max(rec["times_watched"], nb)
                if not rec["seen_date"] and seen_date:
                    rec["seen_date"] = seen_date
    return sorted(eps.values(),
                  key=lambda e: (str(e["show"]).lower(), e["season"] or 0, e["number"] or 0))


def _find_profile(cache) -> dict:
    for _k, _s, _age, d in cache:
        if not isinstance(d, dict):
            continue
        cand = d.get("data", d)
        if isinstance(cand, dict) and ("is_vip" in cand or "is_premium" in cand):
            return {"name": cand.get("name", ""), "id": cand.get("id", ""),
                    "avatar": cand.get("avatar", ""), "is_vip": cand.get("is_vip"),
                    "is_premium": cand.get("is_premium")}
    return {}


def parse_library(diocache: Path) -> dict:
    cache = load_cache(diocache)
    movies = _build_movies(cache)
    series = _build_series(cache)
    watch_events = _build_watch_events(cache)
    episode_details = _build_episodes(cache)
    profile = _find_profile(cache)

    # Attach the cached individual episodes to their show.
    by_show: dict = {}
    for e in episode_details:
        by_show.setdefault(e["show_id"], []).append(e)
    for s in series:
        s["episodes"] = by_show.get(s["id"], [])

    total_watched_eps = sum(int(s["watched_eps"]) for s in series if str(s["watched_eps"]).isdigit())
    stats = {
        "movies": len(movies),
        "series": len(series),
        "episodes": total_watched_eps,
        "watchlist": sum(1 for m in movies if m["watch_later"]) + sum(1 for s in series if s["for_later"]),
        "favorites": sum(1 for s in series if s["favorite"]),
        "archived": sum(1 for s in series if s["archived"]),
        "watch_events": len(watch_events),
        "episode_details": len(episode_details),
        "episode_details_seen": sum(1 for e in episode_details if e["seen"]),
        "cache_entries": len(cache),
    }
    return {"movies": movies, "series": series, "watch_events": watch_events,
            "episodes": episode_details, "profile": profile, "stats": stats}


# --------------------------------------------------------------------------
# Output writers
# --------------------------------------------------------------------------
def _csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = dict(r)
            if isinstance(row.get("genres"), list):
                row["genres"] = ", ".join(row["genres"])
            w.writerow(row)


def write_csvs(lib: dict, out: Path) -> None:
    movie_fields = ["title", "year", "genres", "watched", "watch_later", "watched_at",
                    "rewatch_count", "rating", "runtime_min", "imdb_id", "overview"]
    series_fields = ["title", "watched_eps", "aired_eps", "status", "progress", "up_to_date",
                     "favorite", "archived", "for_later", "watchedDate"]
    _csv(out / "movies.csv", lib["movies"], movie_fields)
    _csv(out / "series.csv", lib["series"], series_fields)
    _csv(out / "watch_history.csv", lib["watch_events"],
         ["entity_type", "watched_at", "created_at", "runtime_min", "uuid"])
    _csv(out / "episodes.csv", lib["episodes"],
         ["show", "season", "number", "name", "seen", "seen_date", "times_watched",
          "air_date", "show_id", "episode_id"])
    (out / "profile.json").write_text(json.dumps(lib["profile"], ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(lib["stats"], ensure_ascii=False, indent=2),
                                      encoding="utf-8")


def write_report(lib: dict, out: Path) -> None:
    s, p = lib["stats"], lib["profile"]
    L = []
    L.append("# TV Time - recovered data\n")
    L.append(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    if p.get("name"):
        L.append(f"Account: {p['name']} (id {p.get('id','')})")
    L.append("")
    L.append("## Summary")
    L.append(f"- Movies: {s['movies']}")
    L.append(f"- Series: {s['series']}")
    L.append(f"- Watched episodes (series): {s['episodes']}")
    L.append(f"- On the watchlist: {s['watchlist']}")
    L.append(f"- Archived series: {s['archived']}")
    L.append(f"- Watch events: {s['watch_events']}")
    L.append(f"- Individual episodes cached (partial): {s['episode_details']} "
             f"({s['episode_details_seen']} watched)")
    L.append("")
    L.append("Note: TV Time stored the watched/aired counts for every series, plus a small "
             "window of individual episodes near your current progress. The full per-episode "
             "history for all shows was not kept in the backup.")
    L.append("")
    L.append("## Most-watched series")
    L.append("")
    L.append("| Series | Watched | Aired | Status | Last watched |")
    L.append("|---|---:|---:|---|---|")
    top = sorted(lib["series"],
                 key=lambda x: int(x["watched_eps"]) if str(x["watched_eps"]).isdigit() else -1,
                 reverse=True)[:30]
    for x in top:
        L.append(f"| {x['title']} | {x['watched_eps']} | {x['aired_eps']} | {x['status']} | {x['watchedDate']} |")
    L.append("")
    L.append("## Recently watched movies")
    L.append("")
    L.append("| Movie | Year | Watched on | Rewatches |")
    L.append("|---|---|---|---:|")
    mv = sorted([m for m in lib["movies"] if m["watched_at"]],
                key=lambda m: m["watched_at"], reverse=True)[:25]
    for m in mv:
        L.append(f"| {m['title']} | {m['year']} | {m['watchedDate']} | {m['rewatch_count']} |")
    L.append("")
    L.append("## Files")
    L.append("- TVTime.html - open this to browse everything with posters")
    L.append("- movies.csv, series.csv, watch_history.csv, episodes.csv - spreadsheets")
    L.append("- profile.json, summary.json")
    L.append("- raw_files/ - the app files taken from the backup")
    (out / "TVTime-Recovered-Data.md").write_text("\n".join(L) + "\n", encoding="utf-8")
