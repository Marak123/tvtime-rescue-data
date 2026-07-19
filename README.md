# TV Time Rescue

Recover your TV Time movies, series and watch history from a local iPhone or iPad backup, and browse them again on a simple web page with posters.

TV Time shut down in July 2026 and a lot of people lost access to years of tracking. If the app is still installed on your phone with its data, there is a good chance you can get most of it back. This tool reads a normal iTunes/Finder/iMazing backup of your device and pulls the TV Time data out of it.

Polish version of this guide: [README.pl.md](README.pl.md)

> Note: this is a small project put together quickly with the help of AI to help people rescue their TV Time data after the shutdown. It is not affiliated with TV Time or its owners. It only reads your backup, it never changes your phone or the backup. Use it on data you own.

## Can I still get my data back?

Read this first, because timing matters.

- If TV Time is STILL installed on your phone and you have NOT deleted it, reset the phone, or reinstalled the app, your data is very likely still on the device. Make a backup now and this tool can probably recover most or all of it.
- If you already have a computer backup of the phone from before the app was removed, you can use that backup directly.
- If you deleted the app, wiped the phone, or restored it, the local data is probably gone and this tool cannot help. There is nothing to read.

The data comes from the app's local cache, so it reflects what the app had last loaded (your library, series progress, watch history). It is usually complete or close to complete, but it is not a guaranteed full account export.

## What you get

- `TVTime.html` - one file you open in your browser to look through everything: posters, titles, descriptions, genres, watched dates, and episode progress for every series. Has search, sorting, filters (Movies, Series, Watchlist, Favorites, Archived), and an Episodes tab that lists the individual episodes with a watched / not watched marker where the backup kept them.
- `movies.csv`, `series.csv`, `watch_history.csv`, `episodes.csv` - spreadsheets you can open in Excel or import somewhere else (for example Trakt or Serializd).
- `TVTime-Recovered-Data.md` - a short readable report.
- `raw_files/` - the actual app files taken from the backup (the database and preferences), in case you want them.

## What you need

- Your iPhone or iPad with TV Time still installed, OR an existing backup of it.
- A computer (Windows, Mac, or Linux).
- A free tool to make the backup: Finder (Mac), Apple Devices or iTunes (Windows), or iMazing (Windows and Mac).
- About 15 minutes.

Making the backup UNENCRYPTED is the easy path and needs no password. Encrypted backups also work, you just type the backup password when the tool asks. See "Make a backup" below.

## Quick start

There are two ways to run it. Pick one.

### Option A: download the ready-made program (no Python needed)

1. Go to the [Releases page](https://github.com/Marak123/tvtime-rescue/releases) and download the file for your system:
   - Windows: `tvtime-rescue-windows.exe`
   - Mac: `tvtime-rescue-macos`
   - Linux: `tvtime-rescue-linux`
2. Make a backup of your device (see below).
3. Double-click the program and follow the questions on screen. It will find your backup, ask where to save, do the work, and tell you which file to open.

On Mac the first time, right-click the file and choose Open, then confirm, because it is not signed by Apple. On Linux, run `chmod +x tvtime-rescue-linux` first.

### Option B: run from the Python source

You need Python 3.9 or newer from [python.org](https://www.python.org/downloads/).

```
git clone https://github.com/Marak123/tvtime-rescue.git
cd tvtime-rescue
pip install -r requirements.txt
python run.py
```

`python run.py` with no options walks you through everything. If you prefer to type the paths yourself:

```
python run.py --backup "PATH_TO_BACKUP_FOLDER" --output "PATH_TO_RESULTS_FOLDER"
```

The double-click launchers in the `scripts/` folder do the same thing: `START-HERE-Windows.bat`, `START-HERE-Mac.command`, `START-HERE-Linux.sh`.

## Make a backup (step by step)

Full guides with screenshots-style steps:

- [iMazing (Windows or Mac, free)](docs/imazing.md)
- [Finder on Mac](docs/finder-mac.md)
- [Apple Devices or iTunes on Windows](docs/windows-apple-devices.md)

Short version:

1. Connect the phone by cable and trust the computer.
2. Choose "back up to this computer" (not iCloud).
3. Recommended: leave "encrypt local backup" turned OFF. This makes recovery simplest.
4. Start the backup and wait for it to finish completely.
5. Point this tool at the backup folder (it contains a file called `Manifest.db`). The tool can also find it for you automatically in the standard locations.

If your backup is encrypted, that is fine too. The tool detects it and asks for the backup password. For that case you also need the decryption support installed: `pip install iphone-backup-decrypt` (it is already in `requirements.txt`, and the downloaded program has it built in).

## Where backups live (if you want to find the folder yourself)

- Windows (Apple Devices / iTunes): `%APPDATA%\Apple Computer\MobileSync\Backup` or `%USERPROFILE%\Apple\MobileSync\Backup`
- Mac (Finder): `~/Library/Application Support/MobileSync/Backup`
- iMazing: set your own folder when backing up, or use iMazing's "reveal in Finder/Explorer" on the backup.

Each backup is a folder named with a long device id. The right folder is the one that contains `Manifest.db` and `Info.plist`.

## Privacy

Everything runs on your own computer. Nothing is uploaded. The results contain your personal viewing history, so keep them to yourself. Do not commit the `raw_files/` folder, the CSVs, or `profile.json` to a public place. The web page loads poster images from thetvdb.com, which means your browser fetches those images over the internet the first time you open it; the page itself stays on your machine.

## How it works (short version)

TV Time is a Flutter app. It stores a local cache of the server responses in a small SQLite database called `DioCache.db` (Dio is the HTTP client it uses). Those responses are plain JSON and include your library, your per-series episode progress, and your watch history. The tool copies `DioCache.db` out of the backup, reads that JSON, and turns it into spreadsheets and a web page. For unencrypted backups it reads the files directly; for encrypted backups it uses the backup password to decrypt them.

## Build the program yourself

If you would rather build the standalone executable instead of downloading it:

```
pip install -r requirements.txt pyinstaller
python scripts/build_exe.py
```

The file appears in `dist/`. You can only build for the system you are on (build the Windows exe on Windows, and so on). The GitHub Actions workflow in this repo builds all three automatically when a release tag is pushed.

## Limitations

- iOS and iPadOS only for now. Android stores this data differently and is not supported yet.
- The data is from the app cache, so very recent changes that never loaded might be missing. Numbers are usually complete or close to it.
- TV Time did not keep series descriptions in the cache, so series show a poster, title and episode progress, while movies also have full descriptions.
- Per-episode watched/not-watched detail is only partial. TV Time stored the total watched and aired count for every series, but it kept individual episodes only around your current position (the up-next queue and recently watched). So the Episodes tab shows the episodes that were cached, not the full episode-by-episode history of every show.
- The recovered data is a snapshot for your own records. This is not a way to restore data back into TV Time.

## Credits

**Built quickly with the help of AI** to help the community after the TV Time shutdown. Based on the well-understood structure of iOS backups and the app's local cache. Uses [iphone-backup-decrypt](https://github.com/jsharkey13/iphone_backup_decrypt) for encrypted backups. Not affiliated with TV Time. All trademarks belong to their owners.

## License

MIT. See [LICENSE](LICENSE).
