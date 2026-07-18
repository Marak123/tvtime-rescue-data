# Make a backup with Finder (Mac)

On modern macOS there is no iTunes. You make device backups in Finder.

## Steps

1. Connect your iPhone or iPad with a cable. Unlock it and tap "Trust" if asked.
2. Open Finder. Your device appears in the left sidebar under "Locations". Click it.
3. In the "General" tab, under Backups, choose:
   "Back up all of the data on your iPhone to this Mac."
4. Recommended: leave "Encrypt local backup" UNCHECKED. This is the simplest path and needs no password. Encrypted backups also work with this tool, you will just type the password later.
5. Click "Back Up Now".
6. Wait until it finishes completely before disconnecting.

## Find the backup folder

This tool can find it automatically. If you want the folder yourself, it is here:

```
~/Library/Application Support/MobileSync/Backup/
```

Inside there is one folder per backup, named with a long device id. The right one contains `Manifest.db` and `Info.plist`.

Tip: in Finder use the menu Go > Go to Folder and paste the path above.

## Next

Run the tool (the downloaded program, or `python run.py`) and point it at the backup folder, or let it find the backup for you.
