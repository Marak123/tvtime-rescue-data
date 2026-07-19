# TV Time Rescue

Odzyskaj swoje filmy, seriale i historię oglądania z TV Time z lokalnego backupu iPhone lub iPada, a potem przeglądaj je znowu na prostej stronie z plakatami.

TV Time zostało zamknięte w lipcu 2026 i wiele osób straciło dostęp do lat śledzenia seriali. Jeśli aplikacja nadal jest zainstalowana na telefonie razem z danymi, jest duża szansa, że da się większość odzyskać. To narzędzie czyta zwykły backup urządzenia (iTunes, Finder lub iMazing) i wyciąga z niego dane TV Time.

English version: [README.md](README.md)

> Uwaga: to niewielki projekt zrobiony szybko z pomocą AI, żeby pomóc ludziom uratować dane z TV Time po zamknięciu usługi. Nie jest powiązany z TV Time ani jego właścicielami. Narzędzie tylko czyta backup, nigdy nie zmienia telefonu ani samego backupu. Używaj go na własnych danych.

## Czy da się jeszcze odzyskać dane?

Przeczytaj to najpierw, bo liczy się czas.

- Jeśli TV Time NADAL jest zainstalowane na telefonie i NIE zostało usunięte, telefon nie był resetowany, a aplikacja nie była instalowana od nowa, dane najpewniej wciąż są na urządzeniu. Zrób teraz backup, a to narzędzie prawdopodobnie odzyska większość lub całość.
- Jeśli masz już backup telefonu na komputerze zrobiony zanim aplikacja zniknęła, możesz użyć go bezpośrednio.
- Jeśli aplikacja została usunięta, telefon wyczyszczony albo przywrócony, dane lokalne są najpewniej stracone i narzędzie nie pomoże. Nie ma czego czytać.

Dane pochodzą z lokalnego cache aplikacji, więc odzwierciedlają to, co aplikacja ostatnio wczytała (biblioteka, postęp seriali, historia oglądania). Zwykle są kompletne lub prawie kompletne, ale to nie jest gwarantowany pełny eksport konta.

## Co dostajesz

- `TVTime.html` - jeden plik, który otwierasz w przeglądarce, żeby przejrzeć wszystko: plakaty, tytuły, opisy, gatunki, daty obejrzenia i postęp odcinków dla każdego serialu. Ma wyszukiwarkę, sortowanie, filtry (Filmy, Seriale, Do obejrzenia, Ulubione, Archiwum) oraz zakładkę Episodes, która pokazuje pojedyncze odcinki ze znacznikiem obejrzany / nieobejrzany tam, gdzie backup je zapisał.
- `movies.csv`, `series.csv`, `watch_history.csv`, `episodes.csv` - arkusze, które otworzysz w Excelu lub zaimportujesz gdzie indziej (na przykład Trakt albo Serializd).
- `TVTime-Recovered-Data.md` - krótki czytelny raport.
- `raw_files/` - same pliki aplikacji wyjęte z backupu (baza danych i ustawienia), gdybyś ich potrzebował.

## Czego potrzebujesz

- iPhone lub iPad z nadal zainstalowanym TV Time, ALBO gotowy backup urządzenia.
- Komputer (Windows, Mac lub Linux).
- Darmowe narzędzie do zrobienia backupu: Finder (Mac), Apple Devices lub iTunes (Windows), albo iMazing (Windows i Mac).
- Około 15 minut.

Najprostsza droga to backup NIEZASZYFROWANY, bo nie wymaga hasła. Zaszyfrowane też działają, po prostu wpisujesz hasło backupu, gdy narzędzie o nie poprosi. Zobacz sekcję "Zrób backup".

## Szybki start

Są dwa sposoby uruchomienia. Wybierz jeden.

### Sposób A: pobierz gotowy program (bez instalowania Pythona)

1. Wejdź na [stronę Releases](https://github.com/Marak123/tvtime-rescue/releases) i pobierz plik dla swojego systemu:
   - Windows: `tvtime-rescue-windows.exe`
   - Mac: `tvtime-rescue-macos`
   - Linux: `tvtime-rescue-linux`
2. Zrób backup urządzenia (patrz niżej).
3. Kliknij dwa razy w program i odpowiadaj na pytania na ekranie. Znajdzie backup, zapyta gdzie zapisać, zrobi swoje i powie który plik otworzyć.

Na Macu za pierwszym razem kliknij plik prawym przyciskiem i wybierz Otwórz, potem potwierdź, bo plik nie jest podpisany przez Apple. Na Linuksie najpierw zrób `chmod +x tvtime-rescue-linux`.

### Sposób B: uruchom z kodu w Pythonie

Potrzebujesz Pythona 3.9 lub nowszego z [python.org](https://www.python.org/downloads/).

```
git clone https://github.com/Marak123/tvtime-rescue.git
cd tvtime-rescue
pip install -r requirements.txt
python run.py
```

`python run.py` bez opcji przeprowadzi Cię przez wszystko. Jeśli wolisz podać ścieżki samodzielnie:

```
python run.py --backup "SCIEZKA_DO_FOLDERU_BACKUPU" --output "SCIEZKA_DO_FOLDERU_WYNIKOW"
```

Launchery do dwukliku w folderze `scripts/` robią to samo: `START-HERE-Windows.bat`, `START-HERE-Mac.command`, `START-HERE-Linux.sh`.

## Zrób backup (krok po kroku)

Pełne przewodniki:

- [iMazing (Windows lub Mac, darmowy)](docs/imazing.md)
- [Finder na Macu](docs/finder-mac.md)
- [Apple Devices lub iTunes na Windows](docs/windows-apple-devices.md)

W skrócie:

1. Podłącz telefon kablem i zaufaj komputerowi.
2. Wybierz "kopia na tym komputerze" (nie iCloud).
3. Zalecane: zostaw "szyfruj lokalną kopię" WYŁĄCZONE. Tak jest najprościej.
4. Uruchom backup i poczekaj aż w pełni się zakończy.
5. Wskaż narzędziu folder backupu (zawiera plik `Manifest.db`). Narzędzie potrafi też znaleźć go samo w standardowych lokalizacjach.

Jeśli backup jest zaszyfrowany, to też w porządku. Narzędzie to wykryje i poprosi o hasło backupu. Do tego przypadku potrzebna jest jeszcze obsługa deszyfrowania: `pip install iphone-backup-decrypt` (jest już w `requirements.txt`, a pobrany program ma to wbudowane).

## Gdzie leżą backupy (jeśli chcesz znaleźć folder sam)

- Windows (Apple Devices / iTunes): `%APPDATA%\Apple Computer\MobileSync\Backup` albo `%USERPROFILE%\Apple\MobileSync\Backup`
- Mac (Finder): `~/Library/Application Support/MobileSync/Backup`
- iMazing: ustaw własny folder przy backupie, albo użyj w iMazing opcji "pokaż w Finderze/Eksploratorze".

Każdy backup to folder o długiej nazwie z identyfikatorem urządzenia. Właściwy folder to ten, który zawiera `Manifest.db` i `Info.plist`.

## Prywatność

Wszystko dzieje się na Twoim komputerze. Nic nie jest wysyłane. Wyniki zawierają Twoją historię oglądania, więc zachowaj je dla siebie. Nie wrzucaj folderu `raw_files/`, plików CSV ani `profile.json` w miejsce publiczne. Strona ładuje plakaty z thetvdb.com, czyli przeglądarka pobiera te obrazki z internetu przy pierwszym otwarciu; sama strona zostaje na Twoim komputerze.

## Jak to działa (w skrócie)

TV Time to aplikacja we Flutterze. Trzyma lokalny cache odpowiedzi serwera w małej bazie SQLite o nazwie `DioCache.db` (Dio to klient HTTP, którego używa). Te odpowiedzi to czysty JSON i zawierają Twoją bibliotekę, postęp odcinków per serial oraz historię oglądania. Narzędzie kopiuje `DioCache.db` z backupu, czyta ten JSON i zamienia go na arkusze i stronę. Dla backupów niezaszyfrowanych czyta pliki bezpośrednio; dla zaszyfrowanych używa hasła backupu, żeby je odszyfrować.

## Zbuduj program samodzielnie

Jeśli wolisz zbudować samodzielny plik wykonywalny zamiast go pobierać:

```
pip install -r requirements.txt pyinstaller
python scripts/build_exe.py
```

Plik pojawi się w `dist/`. Budujesz tylko dla systemu, na którym jesteś (exe dla Windows na Windows, i tak dalej). Workflow GitHub Actions w tym repo buduje wszystkie trzy automatycznie po wypchnięciu taga wydania.

## Ograniczenia

- Na razie tylko iOS i iPadOS. Android trzyma te dane inaczej i nie jest jeszcze obsługiwany.
- Dane pochodzą z cache aplikacji, więc bardzo świeże zmiany, które nigdy się nie wczytały, mogą nie być zapisane. Liczby zwykle są kompletne lub bliskie kompletu.
- TV Time nie trzymał opisów seriali w cache, więc seriale mają plakat, tytuł i postęp odcinków, a filmy dodatkowo pełne opisy.
- Szczegóły „który odcinek obejrzany, a który nie" są tylko częściowe. TV Time zapisywał sumę obejrzanych i wyemitowanych odcinków dla każdego serialu, ale pojedyncze odcinki trzymał tylko wokół Twojego bieżącego postępu (kolejka „do obejrzenia" i ostatnio obejrzane). Dlatego zakładka Episodes pokazuje odcinki, które trafiły do cache, a nie pełną historię odcinek po odcinku dla każdego serialu.
- Odzyskane dane to snapshot dla Twoich potrzeb. To nie jest sposób na przywrócenie danych z powrotem do TV Time.

## Podziękowania

**Zrobione szybko z pomocą AI**, żeby pomóc społeczności po zamknięciu TV Time. Oparte na dobrze znanej strukturze backupów iOS i lokalnego cache aplikacji. Do backupów zaszyfrowanych używa [iphone-backup-decrypt](https://github.com/jsharkey13/iphone_backup_decrypt). Niepowiązane z TV Time. Wszystkie znaki towarowe należą do ich właścicieli.

## Licencja

MIT. Zobacz [LICENSE](LICENSE).
