# Exporting to Trakt, Letterboxd and Simkl

After a recovery, the tool writes ready-to-import files into an `exports` folder,
with one subfolder per platform. Each subfolder has its own short README with the
exact steps. You can also (re)build them at any time from an existing recovery:

```
python run.py export --input "PATH_TO_RECOVERED_FOLDER"
```

Pick specific platforms with `--platform`:

```
python run.py export --input "PATH_TO_RECOVERED_FOLDER" --platform simkl,letterboxd
```

The exporters read `library.json` from the recovered folder, so they do not need
the backup again.

## Which platform gets what

| Platform   | Movies | Series | Per-episode history |
|------------|--------|--------|---------------------|
| Letterboxd | Yes    | No (films only) | n/a |
| Simkl      | Yes    | Yes, with status and last-episode-watched | Reconstructed from your counts |
| Trakt      | Yes    | Added to watchlist | Only the episodes the backup recorded |

Movies transfer cleanly everywhere because we have IMDb ids, watched dates,
ratings and rewatch flags.

For TV series, remember what the backup actually held: how many episodes of each
show you watched, plus the handful of episodes around your current position. So:

- Simkl is the best target for series. It uses the same count-based model as TV
  Time, so we set each show's status (watching, completed, hold, plan to watch)
  and a last-episode-watched from the count. This is most accurate when the
  library was enriched with a TheTVDB key (full episode lists); otherwise the
  last episode falls back to whatever the backup explicitly recorded.
- Trakt wants exact episodes. We add your shows to the Trakt watchlist and mark
  the specific episodes the backup recorded as watched. We do not invent the
  rest, so Trakt will not show a full per-episode history from the backup alone.

## Files per platform

Letterboxd (`exports/letterboxd`):
- `letterboxd_diary.csv` - watched films with dates, ratings, rewatch flags
- `letterboxd_watchlist.csv` - films on your watchlist

Simkl (`exports/simkl`):
- `simkl_import.csv` - movies and series in Simkl's import format

Trakt (`exports/trakt`):
- `trakt_sync.json` - everything in Trakt's sync-API shape
- `trakt_movies_history.csv`, `trakt_movies_watchlist.csv`, `trakt_movies_ratings.csv`
- `trakt_shows_watchlist.csv`, `trakt_episodes_history.csv`

## Privacy

These files are your personal viewing history. Keep them to yourself and do not
commit them to a public repository.
