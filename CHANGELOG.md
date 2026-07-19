# Changelog

## 0.1.2

- Optional enrichment from TheTVDB. Add a free API key in a `.env` file
  (`TVDB_API_KEY=...`), or pass `--tvdb-key`, or set the `TVDB_API_KEY`
  environment variable, and the tool fills in the gaps the backup could not:
  series descriptions and genres, and the full season and episode list for
  every show. Your real watched status from the backup is overlaid on top;
  episodes the backup never recorded are shown as unknown, not guessed.
- Responses are cached in a `tvdb_cache` folder so re-runs are fast.
- Series detail view now groups episodes by season and shows three states:
  watched, not watched, and unknown.
- Uses only the Python standard library for the API calls, so there is no new
  dependency and the executable stays small. Works fully without a key.

## 0.1.1

- New Episodes tab and per-series episode list showing the individual episodes
  TV Time cached around your current progress, each marked watched or not
  watched with the date, plus a Watched / Not watched filter.
- Added `episodes.csv`.
- The report and README state clearly that this per-episode detail is partial
  (the counts are complete, the full per-episode history is not in the backup).

## 0.1.0

- Recover TV Time movies, series and watch history from a local iOS backup,
  supporting both unencrypted and encrypted backups.
- CSV exports, a Markdown report, and a single self-contained HTML page for
  browsing the library with posters.
- Interactive command line walkthrough, double-click launchers for Windows,
  Mac and Linux, a PyInstaller build script and a GitHub Actions workflow that
  builds standalone executables for all three systems.
