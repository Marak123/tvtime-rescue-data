# Make a backup with iMazing (Windows or Mac)

iMazing is free for making and browsing backups. This is a good option on Windows if you do not want iTunes, and it works on Mac too.

## Steps

1. Download and install iMazing from the official site (imazing.com).
2. Connect your iPhone or iPad with a cable. Unlock it and tap "Trust" if asked.
3. In iMazing, select your device in the left sidebar.
4. Click "Back Up".
5. When it asks about options:
   - Choose to back up to this computer.
   - Recommended: turn OFF backup encryption. This makes recovery simplest and needs no password. If a password box is greyed out or forced on, that is because your device already has "Encrypt local backup" enabled; encrypted backups still work with this tool, you will just enter the password later.
6. Start the backup and wait until it finishes completely. A large library can take a while.

## Find the backup folder

This tool can usually find the backup automatically. If you need the folder yourself:

- In iMazing, right-click the latest backup and look for an option like "Reveal in Finder" or "Show in Explorer", or check iMazing's backup location in its preferences.
- The correct folder is the one that directly contains `Manifest.db` and `Info.plist`.

Note: iMazing sometimes stores backups in its own wrapped format. If the folder you find does not contain `Manifest.db` directly, use iMazing's export, or make a standard backup with Finder (Mac) or Apple Devices/iTunes (Windows) instead. See the other guides.

## Next

Run the tool (the downloaded program, or `python run.py`) and point it at the backup folder. It will do the rest.
