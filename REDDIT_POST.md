Suggested title:
If TV Time is still installed on your phone, you can probably still get your data back (free tool)

---

Body:

Like a lot of you, I lost access to years of TV Time tracking when the service shut down. But here is the important part: the app kept a local copy of your library and watch history on your phone. If TV Time is STILL installed and you have not deleted it, reset the phone, or reinstalled the app, that data is almost certainly still there. You just need to get it out before anything happens to it.

So I put together a small free tool to do exactly that. To be upfront: I built it quickly with the help of AI to solve my own problem, then cleaned it up so others can use it. It is open source, it runs entirely on your own computer, and it never uploads anything or changes your phone.

What it recovers:
- Your movies and series with posters and descriptions
- Per-series episode progress (watched vs aired)
- Watch history with dates
- Your watchlist, favorites and archived shows
- Everything as CSV files (easy to import into Trakt, Serializd, etc.) plus a single web page you open in your browser to look through it all with posters

How it works in one line: TV Time stored its data in a local cache on the device, and a normal iPhone/iPad backup contains that cache. The tool reads the backup and pulls the data out.

What you do:
1. Make a local backup of your iPhone/iPad with Finder, Apple Devices/iTunes, or the free iMazing. An unencrypted backup is the simplest, but encrypted works too (you just enter the backup password).
2. Run the tool and point it at the backup. It walks you through everything.
3. Open the web page it makes.

Ready-made programs for Windows, Mac and Linux are on the Releases page, so you do not need to install Python. Source and full step-by-step instructions here:

https://github.com/Marak123/tvtime-rescue

Two honest caveats: it reads the app cache, so it reflects what the app last loaded (usually complete or very close). And if you already deleted the app or wiped the phone, the local data is likely gone and there is nothing to read. iOS/iPadOS only for now, Android stores this differently.

If it helps you get your list back, great. Happy to answer questions in the comments.
