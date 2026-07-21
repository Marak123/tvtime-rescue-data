"""Command line interface for TV Time Rescue.

Subcommands:
  recover   read a backup and build everything (default when none is given)
  export    turn an existing recovery into import files for other platforms
  site      rebuild the HTML page from an existing recovery
"""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from . import __version__
from .extract import enrich
from .extract.backup import (
    BackupError,
    extract_tvtime,
    find_backups,
    is_encrypted,
    looks_like_backup,
)
from .extract.parse import parse_library, write_csvs, write_report
from .exporters import load_library, run_exports, save_library
from .viewer import build_site

ALL_PLATFORMS = ("letterboxd", "simkl", "trakt")

BANNER = r"""
==================================================================
  TV Time Rescue  v{ver}
  Recover your TV Time movies and series from a local iOS backup.
==================================================================
""".strip("\n")


def _pick_backup_interactive() -> Path:
    print("\nLooking for iPhone/iPad backups on this computer...")
    backups = find_backups()
    if backups:
        print(f"Found {len(backups)} backup(s):\n")
        for i, b in enumerate(backups, 1):
            enc = "ENCRYPTED" if b.encrypted else "unencrypted"
            tv = "TV Time installed" if b.has_tvtime else "TV Time NOT listed"
            print(f"  [{i}] {b.device_name} - {b.product} iOS {b.ios_version}")
            print(f"      last backup: {b.last_backup}  ({enc}, {tv})")
            print(f"      {b.path}")
        print("  [0] Enter a folder path myself")
        while True:
            choice = input("\nChoose a backup number: ").strip()
            if choice == "0":
                break
            if choice.isdigit() and 1 <= int(choice) <= len(backups):
                return backups[int(choice) - 1].path
            print("  Please type one of the numbers shown above.")
    else:
        print("No backups found in the standard locations.")
        print("Make a backup first (see the README), or paste the backup folder path below.")

    while True:
        raw = input("\nPaste the full path to the backup folder: ").strip().strip('"')
        if not raw:
            continue
        folder = Path(raw).expanduser()
        if looks_like_backup(folder):
            return folder
        print(f"  '{folder}' has no Manifest.db / Info.plist. That is not a backup folder.")


def _default_output() -> Path:
    base = Path.home() / "Documents"
    if not base.is_dir():
        base = Path.home()
    return base / "TVTime-Recovered"


def run(backup_dir: Path, output_dir: Path, password: str | None, make_site: bool,
        tvdb_key: str | None = None, tvdb_pin: str | None = None,
        do_export: bool = True) -> dict:
    raw_dir = output_dir / "raw_files"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1] Reading the backup and copying TV Time files...")
    if is_encrypted(backup_dir) and not password:
        print("    This backup is ENCRYPTED. Please enter the backup password.")
        password = getpass.getpass("    Backup password: ")
    extract_tvtime(backup_dir, raw_dir, passphrase=password, log=lambda m: print(m))

    print("\n[2] Parsing your library (DioCache.db)...")
    lib = parse_library(raw_dir / "DioCache.db")

    print("[3] Enriching series from TheTVDB...")
    if tvdb_key:
        try:
            client = enrich.make_client(tvdb_key, tvdb_pin, output_dir / "tvdb_cache")
            client.login()
            enrich.enrich_library(lib, client, log=lambda m: print(m))
        except Exception as exc:  # never let enrichment break the recovery
            print(f"    TVDB enrichment skipped ({type(exc).__name__}: {exc}).")
            print("    The rest of your data was still recovered from the backup.")
    else:
        print("    No TVDB key found - skipping (add one in .env to enable, see README).")

    print("[4] Writing spreadsheets, report and library.json...")
    write_csvs(lib, output_dir)
    write_report(lib, output_dir)
    save_library(lib, output_dir / "library.json")

    if make_site:
        print("[5] Building the browsable web page...")
        build_site(lib, output_dir / "TVTime.html")

    if do_export:
        print("[6] Creating import files for Letterboxd, Simkl and Trakt...")
        run_exports(lib, output_dir / "exports", ALL_PLATFORMS, log=lambda m: print(m))

    return lib


def _print_result(lib: dict, output_dir: Path) -> None:
    s = lib["stats"]
    print("\n==================================================================")
    print("  Done. Here is what was recovered:")
    print(f"    Movies:            {s['movies']}")
    print(f"    Series:            {s['series']}")
    print(f"    Watched episodes:  {s['episodes']}")
    print(f"    Watchlist:         {s['watchlist']}")
    print("==================================================================")
    print("\n  Browse everything with posters:")
    print(f"    {output_dir / 'TVTime.html'}")
    print("\n  Import files for other platforms:")
    print(f"    {output_dir / 'exports'}  (letterboxd, simkl, trakt)")
    print(f"\n  All files are in:\n    {output_dir}\n")


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def _cmd_recover(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="tvtime-rescue recover",
        description="Recover your TV Time library from a local iOS backup "
                    "(unencrypted or encrypted).",
    )
    ap.add_argument("--backup", help="Path to the backup folder (contains Manifest.db).")
    ap.add_argument("--output", help="Where to write the results.")
    ap.add_argument("--password", help="Backup password (encrypted backups).")
    ap.add_argument("--no-site", action="store_true", help="Do not build the HTML page.")
    ap.add_argument("--no-export", action="store_true", help="Do not build platform import files.")
    ap.add_argument("--tvdb-key", help="TheTVDB API key (or set TVDB_API_KEY / use .env).")
    ap.add_argument("--tvdb-pin", help="TheTVDB subscriber PIN, only for user-supported keys.")
    ap.add_argument("--no-tvdb", action="store_true", help="Do not contact TheTVDB even if a key is set.")
    args = ap.parse_args(argv)

    print(BANNER.format(ver=__version__))
    interactive = not args.backup
    try:
        backup_dir = Path(args.backup).expanduser() if args.backup else _pick_backup_interactive()
        if args.output:
            output_dir = Path(args.output).expanduser()
        elif interactive:
            default = _default_output()
            raw = input(f"\nWhere should I save the results?\n"
                        f"  [Enter] = {default}\n  path: ").strip().strip('"')
            output_dir = Path(raw).expanduser() if raw else default
        else:
            output_dir = _default_output()

        tvdb_key, tvdb_pin = (None, None)
        if not args.no_tvdb:
            tvdb_key, tvdb_pin = enrich.load_key(args.tvdb_key)
            if args.tvdb_pin:
                tvdb_pin = args.tvdb_pin

        lib = run(backup_dir, output_dir, args.password, not args.no_site,
                  tvdb_key=tvdb_key, tvdb_pin=tvdb_pin, do_export=not args.no_export)
        _print_result(lib, output_dir)
    except BackupError as exc:
        print(f"\nERROR: {exc}\n", file=sys.stderr)
        _pause_if_interactive(interactive)
        return 2
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    except Exception as exc:  # noqa: BLE001 - friendly message, not a traceback
        print(f"\nUNEXPECTED ERROR: {type(exc).__name__}: {exc}\n", file=sys.stderr)
        _pause_if_interactive(interactive)
        return 1
    _pause_if_interactive(interactive)
    return 0


def _cmd_export(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="tvtime-rescue export",
        description="Create import files for other platforms from an existing recovery.",
    )
    ap.add_argument("--input", required=True,
                    help="A recovered output folder (the one containing library.json).")
    ap.add_argument("--output", help="Where to write the export folders "
                                     "(default: an 'exports' folder inside the input).")
    ap.add_argument("--platform", default="all",
                    help="Comma-separated: letterboxd,simkl,trakt - or 'all' (default).")
    args = ap.parse_args(argv)

    lib = load_library(args.input)
    out = Path(args.output).expanduser() if args.output else Path(args.input).expanduser() / "exports"
    platforms = ALL_PLATFORMS if args.platform == "all" else tuple(
        p.strip() for p in args.platform.split(",") if p.strip())
    print("Creating platform import files...")
    run_exports(lib, out, platforms)
    print(f"\nDone. Import files are in:\n    {out}\n")
    return 0


def _cmd_site(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="tvtime-rescue site",
        description="Rebuild the browsable HTML page from an existing recovery.",
    )
    ap.add_argument("--input", required=True, help="A recovered output folder (with library.json).")
    ap.add_argument("--output", help="Output HTML file (default: TVTime.html inside the input).")
    args = ap.parse_args(argv)

    lib = load_library(args.input)
    out = Path(args.output).expanduser() if args.output else Path(args.input).expanduser() / "TVTime.html"
    build_site(lib, out)
    print(f"Wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("-V", "--version"):
        print(f"tvtime-rescue {__version__}")
        return 0
    if argv and argv[0] == "export":
        return _cmd_export(argv[1:])
    if argv and argv[0] == "site":
        return _cmd_site(argv[1:])
    if argv and argv[0] == "recover":
        argv = argv[1:]
    return _cmd_recover(argv)


def _pause_if_interactive(interactive: bool) -> None:
    # When launched by double-click the window would close instantly otherwise.
    if interactive and sys.stdin and sys.stdin.isatty():
        try:
            input("Press Enter to close...")
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    raise SystemExit(main())
