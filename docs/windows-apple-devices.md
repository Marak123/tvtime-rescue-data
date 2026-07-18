# Make a backup on Windows (Apple Devices or iTunes)

On Windows you can use the "Apple Devices" app (from the Microsoft Store) or iTunes. Both make the same kind of backup.

## Steps

1. Install "Apple Devices" from the Microsoft Store, or iTunes from apple.com.
2. Connect your iPhone or iPad with a cable. Unlock it and tap "Trust" if asked.
3. Open the app and select your device.
4. Choose to back up to "This computer" (not iCloud).
5. Recommended: leave "Encrypt local backup" UNCHECKED. Simplest path, no password. Encrypted backups also work with this tool, you will just type the password later.
6. Click "Back Up Now" and wait until it finishes completely.

## Find the backup folder

This tool can find it automatically. If you want the folder yourself, it is in one of these, depending on which app you used:

```
%APPDATA%\Apple Computer\MobileSync\Backup
%APPDATA%\Apple\MobileSync\Backup
%USERPROFILE%\Apple\MobileSync\Backup
```

Paste one of those into the File Explorer address bar. Inside there is one folder per backup, named with a long device id. The right one contains `Manifest.db` and `Info.plist`.

## Next

Run the tool (the downloaded program, or `python run.py`) and point it at the backup folder, or let it find the backup for you.
