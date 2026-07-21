"""Convert the recovered library into import files for other tracking platforms.

Each platform has its own module:
  - letterboxd.py   (movies)
  - simkl.py        (movies and series, with episode progress)
  - trakt.py        (movies, series and known episodes; CSV and sync JSON)
  - imdb.py         (movie ratings and watchlist, in IMDb's CSV layout)
  - json_export.py  (a clean, universal JSON of everything)

They all read the same `library.json` that the extractor writes, so they work
independently of the extraction step.
"""
from .base import load_library, run_exports, save_library
from .imdb import export_imdb
from .json_export import export_json
from .letterboxd import export_letterboxd
from .simkl import export_simkl
from .trakt import export_trakt

__all__ = [
    "load_library", "save_library", "run_exports",
    "export_letterboxd", "export_simkl", "export_trakt",
    "export_imdb", "export_json",
]
