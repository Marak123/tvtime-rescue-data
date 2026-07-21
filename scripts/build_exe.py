#!/usr/bin/env python3
"""Build a single standalone executable with PyInstaller.

Run on the system you want a build for (Windows exe on Windows, etc.):

    pip install -r requirements.txt pyinstaller
    python scripts/build_exe.py

The result is written to dist/. On Windows it is dist/tvtime-rescue.exe,
on Mac and Linux it is dist/tvtime-rescue.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    try:
        import PyInstaller.__main__  # noqa: F401
    except ModuleNotFoundError:
        print("PyInstaller is not installed. Run:  pip install pyinstaller")
        return 1

    # Clean previous build so re-runs are reproducible.
    for folder in ("build", "dist"):
        shutil.rmtree(ROOT / folder, ignore_errors=True)

    args = [
        str(ROOT / "run.py"),
        "--name", "tvtime-rescue",
        "--onefile",
        "--console",
        "--noconfirm",
        "--clean",
        # Bundle every subpackage (extract, viewer, exporters) and the
        # encrypted-backup support with its crypto backend.
        "--collect-submodules", "tvtime_rescue",
        "--collect-all", "iphone_backup_decrypt",
        "--collect-all", "Crypto",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
    ]

    import PyInstaller.__main__ as pyi
    print("Building with PyInstaller...")
    pyi.run(args)

    out = ROOT / "dist"
    built = list(out.glob("tvtime-rescue*"))
    if built:
        print("\nDone. Executable:")
        for b in built:
            print(f"   {b}")
    else:
        print("Build finished but no executable was found in dist/.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
