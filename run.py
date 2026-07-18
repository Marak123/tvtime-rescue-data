#!/usr/bin/env python3
"""Entry point for running from source and for building the standalone executable.

    python run.py                 # interactive, walks you through everything
    python run.py --help          # all options
"""
from tvtime_rescue.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
