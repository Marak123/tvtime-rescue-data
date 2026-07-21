"""Locate an iOS backup, detect encryption, and copy the TV Time app files out.

Works for both unencrypted and encrypted backups:

  * Unencrypted: read Manifest.db directly with sqlite3 and copy the files from
    their hashed paths (backup/<first 2 hex>/<fileID>). No password, no extra
    dependencies.
  * Encrypted: use the optional `iphone-backup-decrypt` package to decrypt the
    file index and the TV Time files with the backup password.

The source backup is never modified. Files are only ever read and copied.
"""
from __future__ import annotations

import csv
import os
import plistlib
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path

TVTIME_BUNDLE = "com.tozelabs.tvshowtime"
PRIMARY_DOMAIN = f"AppDomain-{TVTIME_BUNDLE}"
PLUGIN_PREFIX = f"AppDomainPlugin-{TVTIME_BUNDLE}."

# relativePath in the backup  ->  friendly filename in the output folder.
# DioCache.db is the important one (your library and watch history). The rest
# are bonus files that may help (image cache, preferences, cookies).
WANTED_FILES = {
    "Documents/DioCache.db": "DioCache.db",
    "Library/Application Support/libCachedImageData.db": "libCachedImageData.db",
    "Library/Preferences/com.tozelabs.tvshowtime.plist": "com.tozelabs.tvshowtime.plist",
    "Library/Cookies/Cookies.binarycookies": "Cookies.binarycookies",
}

ESSENTIAL = "Documents/DioCache.db"


class BackupError(Exception):
    pass


@dataclass
class BackupInfo:
    path: Path
    device_name: str
    product: str
    ios_version: str
    last_backup: str
    encrypted: bool
    has_tvtime: bool


# --------------------------------------------------------------------------
# Detection helpers
# --------------------------------------------------------------------------
def looks_like_backup(folder: Path) -> bool:
    return (folder / "Manifest.db").is_file() and (folder / "Info.plist").is_file()


def is_encrypted(backup_dir: Path) -> bool:
    """Authoritative flag from Manifest.plist; fall back to probing Manifest.db."""
    manifest_plist = backup_dir / "Manifest.plist"
    if manifest_plist.is_file():
        try:
            with manifest_plist.open("rb") as fh:
                return bool(plistlib.load(fh).get("IsEncrypted"))
        except Exception:
            pass
    # Fallback: an unencrypted Manifest.db is a readable SQLite file.
    try:
        con = sqlite3.connect(f"file:{(backup_dir / 'Manifest.db').as_posix()}?mode=ro", uri=True)
        con.execute("SELECT 1 FROM Files LIMIT 1")
        con.close()
        return False
    except Exception:
        return True


def read_info(backup_dir: Path) -> BackupInfo:
    name = product = ios = last = ""
    has_tv = False
    info = backup_dir / "Info.plist"
    if info.is_file():
        try:
            with info.open("rb") as fh:
                d = plistlib.load(fh)
            name = str(d.get("Device Name", "") or "")
            product = str(d.get("Product Name", d.get("Product Type", "")) or "")
            ios = str(d.get("Product Version", "") or "")
            lb = d.get("Last Backup Date")
            last = lb.isoformat(sep=" ")[:19] if hasattr(lb, "isoformat") else str(lb or "")
            apps = d.get("Installed Applications", []) or []
            has_tv = TVTIME_BUNDLE in [str(a) for a in apps]
        except Exception:
            pass
    return BackupInfo(
        path=backup_dir,
        device_name=_clean(name),
        product=product,
        ios_version=ios,
        last_backup=last,
        encrypted=is_encrypted(backup_dir),
        has_tvtime=has_tv,
    )


def _clean(text: str) -> str:
    # Device names sometimes contain characters the console cannot print.
    return "".join(ch for ch in text if ch.isprintable()) or "(unknown device)"


def default_backup_locations() -> list[Path]:
    home = Path.home()
    locs: list[Path] = []
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", str(home / "AppData" / "Roaming"))
        locs += [
            Path(appdata) / "Apple Computer" / "MobileSync" / "Backup",
            Path(appdata) / "Apple" / "MobileSync" / "Backup",
            home / "Apple" / "MobileSync" / "Backup",
        ]
    else:  # macOS (Linux has no iTunes but a copied backup folder still works)
        locs += [home / "Library" / "Application Support" / "MobileSync" / "Backup"]
    return [p for p in locs if p.is_dir()]


def find_backups() -> list[BackupInfo]:
    """Scan the standard Finder/iTunes/Apple Devices backup folders."""
    found: list[BackupInfo] = []
    for parent in default_backup_locations():
        for child in sorted(parent.iterdir()):
            if child.is_dir() and looks_like_backup(child):
                found.append(read_info(child))
    return found


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------
def _write_index(rows: list[tuple], backup_dir: Path, out_dir: Path) -> None:
    with (out_dir / "tvtime_file_index.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["fileID", "domain", "relativePath", "flags", "hashed_path", "exists"])
        for file_id, domain, rel, flags in rows:
            hp = backup_dir / str(file_id)[:2] / str(file_id)
            w.writerow([file_id, domain, rel, flags, str(hp), hp.is_file()])


def _extract_unencrypted(backup_dir: Path, out_raw: Path, log) -> dict[str, Path]:
    manifest = backup_dir / "Manifest.db"
    con = sqlite3.connect(f"file:{manifest.as_posix()}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT fileID, domain, relativePath, flags FROM Files "
        "WHERE domain = ? OR domain LIKE ? ORDER BY domain, relativePath",
        (PRIMARY_DOMAIN, PLUGIN_PREFIX + "%"),
    ).fetchall()
    con.close()
    log(f"  Found {len(rows)} TV Time entries in the backup index.")
    _write_index(rows, backup_dir, out_raw.parent)

    copied: dict[str, Path] = {}
    for file_id, domain, rel, flags in rows:
        if flags != 1 or domain != PRIMARY_DOMAIN or rel not in WANTED_FILES:
            continue
        src = backup_dir / str(file_id)[:2] / str(file_id)
        if not src.is_file():
            log(f"  WARNING: data file missing for {rel}")
            continue
        dst = out_raw / WANTED_FILES[rel]
        shutil.copy2(src, dst)
        copied[rel] = dst
        log(f"  Copied {rel}  ->  {dst.name}  ({dst.stat().st_size:,} bytes)")
    return copied


def _extract_encrypted(backup_dir: Path, out_raw: Path, passphrase: str, log) -> dict[str, Path]:
    try:
        from iphone_backup_decrypt import EncryptedBackup
    except ModuleNotFoundError as exc:
        raise BackupError(
            "This backup is encrypted. Install the decryption support first:\n"
            "    pip install iphone-backup-decrypt\n"
            "or make a new UNENCRYPTED backup (see the README)."
        ) from exc

    if not passphrase:
        raise BackupError("This backup is encrypted but no password was provided.")

    log("  Backup is encrypted - unlocking with the password...")
    backup = EncryptedBackup(backup_directory=str(backup_dir), passphrase=passphrase)
    backup.test_decryption()  # raises if the password is wrong

    # Build the file index from the decrypted manifest.
    try:
        with backup.manifest_db_cursor() as cur:
            rows = cur.execute(
                "SELECT fileID, domain, relativePath, flags FROM Files "
                "WHERE domain = ? OR domain LIKE ? ORDER BY domain, relativePath",
                (PRIMARY_DOMAIN, PLUGIN_PREFIX + "%"),
            ).fetchall()
        log(f"  Found {len(rows)} TV Time entries in the backup index.")
        _write_index(rows, backup_dir, out_raw.parent)
    except Exception:
        pass  # the index is a nice-to-have; keep going

    copied: dict[str, Path] = {}
    for rel, name in WANTED_FILES.items():
        dst = out_raw / name
        try:
            backup.extract_file(relative_path=rel, domain_like=PRIMARY_DOMAIN,
                                output_filename=str(dst))
        except Exception as exc:
            log(f"  Skipped {rel} ({type(exc).__name__})")
            continue
        if dst.is_file():
            copied[rel] = dst
            log(f"  Decrypted {rel}  ->  {dst.name}  ({dst.stat().st_size:,} bytes)")
    return copied


def extract_tvtime(backup_dir: Path, out_raw: Path, *, passphrase: str | None = None,
                   log=print) -> dict[str, Path]:
    """Copy the TV Time files out of the backup. Returns {relativePath: local file}."""
    backup_dir = backup_dir.expanduser().resolve()
    if not looks_like_backup(backup_dir):
        raise BackupError(
            f"'{backup_dir}' does not look like an iOS backup folder.\n"
            "It must contain Manifest.db and Info.plist. See the README for how to find it."
        )
    out_raw.mkdir(parents=True, exist_ok=True)

    if is_encrypted(backup_dir):
        copied = _extract_encrypted(backup_dir, out_raw, passphrase or "", log)
    else:
        copied = _extract_unencrypted(backup_dir, out_raw, log)

    if ESSENTIAL not in copied:
        raise BackupError(
            "Could not find Documents/DioCache.db for TV Time in this backup.\n"
            "Make sure TV Time is still installed on the device and that the backup "
            "completed fully, then try again."
        )
    return copied
