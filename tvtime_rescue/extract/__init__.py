"""Data extraction.

Reads a local iOS backup, copies the TV Time app files out, parses DioCache.db
into a structured library, and can optionally enrich it from TheTVDB.
"""
from . import enrich
from .backup import (
    BackupError,
    extract_tvtime,
    find_backups,
    is_encrypted,
    looks_like_backup,
    read_info,
)
from .parse import parse_library, write_csvs, write_report

__all__ = [
    "BackupError", "extract_tvtime", "find_backups", "is_encrypted",
    "looks_like_backup", "read_info", "parse_library", "write_csvs",
    "write_report", "enrich",
]
