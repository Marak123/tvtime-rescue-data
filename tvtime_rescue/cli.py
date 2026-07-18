"""Command line interface and interactive walkthrough for TV Time Rescue."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from . import __version__
from .backup import (
    BackupError,
    find_backups,
    is_encrypted,
    looks_like_backup,
    read_info,
    extract_tvtime,
)
from .parse import parse_library, write_csvs, write_report
from .site import build_site

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
        print(f"  [0] Enter a folder path myself")
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


def run(backup_dir: Path, output_dir: Path, password: str | None, make_site: bool) -> dict:
    raw_dir = output_dir / "raw_files"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] Reading the backup and copying TV Time files...")
    if is_encrypted(backup_dir) and not password:
        print("      This backup is ENCRYPTED. Please enter the backup password.")
        password = getpass.getpass("      Backup password: ")
    extract_tvtime(backup_dir, raw_dir, passphrase=password, log=lambda m: print(m))

    print("\n[2/4] Parsing your library (DioCache.db)...")
    lib = parse_library(raw_dir / "DioCache.db")

    print("[3/4] Writing spreadsheets and report...")
    write_csvs(lib, output_dir)
    write_report(lib, output_dir)

    if make_site:
        print("[4/4] Building the browsable web page...")
        build_site(lib, output_dir / "TVTime.html")
    else:
        print("[4/4] Skipping web page (--no-site).")
    return lib


def _print_result(lib: dict, output_dir: Path) -> None:
    s = lib["stats"]
    print("\n==================================================================")
    print("  Done. Here is what was recovered:")
    print(f"    Movies:            {s['movies']}")
    print(f"    Series:            {s['series']}")
    print(f"    Watched episodes:  {s['episodes']}")
    print(f"    Watchlist:         {s['watchlist']}")
    print(f"    Watch events:      {s['watch_events']}")
    print("==================================================================")
    print(f"\n  Open this file to browse everything with posters:")
    print(f"    {output_dir / 'TVTime.html'}")
    print(f"\n  All files are in:\n    {output_dir}\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="tvtime-rescue",
        description="Recover your TV Time library from a local iOS backup "
                    "(unencrypted or encrypted).",
    )
    ap.add_argument("--backup", help="Path to the backup folder (contains Manifest.db).")
    ap.add_argument("--output", help="Where to write the results.")
    ap.add_argument("--password", help="Backup password (encrypted backups). "
                                       "Leave empty to be asked securely.")
    ap.add_argument("--no-site", action="store_true", help="Do not build the HTML page.")
    ap.add_argument("--version", action="version", version=f"tvtime-rescue {__version__}")
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

        lib = run(backup_dir, output_dir, args.password, not args.no_site)
        _print_result(lib, output_dir)
    except BackupError as exc:
        print(f"\nERROR: {exc}\n", file=sys.stderr)
        _pause_if_interactive(interactive)
        return 2
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    except Exception as exc:  # noqa: BLE001 - show a friendly message, not a traceback
        print(f"\nUNEXPECTED ERROR: {type(exc).__name__}: {exc}\n", file=sys.stderr)
        _pause_if_interactive(interactive)
        return 1

    _pause_if_interactive(interactive)
    return 0


def _pause_if_interactive(interactive: bool) -> None:
    # When launched by double-click the window would close instantly otherwise.
    if interactive and sys.stdin and sys.stdin.isatty():
        try:
            input("Press Enter to close...")
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    raise SystemExit(main())
