# Jellyfin-Welten

[![Spendier mir einen Kaffee](https://img.shields.io/badge/☕_Spendier_mir_einen_Kaffee-PayPal-0070ba?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/DrdotHouse)

*[English version](README.en.md)*

„Welten“ wie bei Disney+ – Marvel, Star Wars, DC, Pixar, Disney, DreamWorks, Illumination, Wizarding World, Mittelerde, James Bond, Jurassic Park, Studio Ghibli, Bud Spencer & Terence Hill, Star Trek, Alien & Predator, Horror-Klassiker – als Liste für das Jellyfin-Plugin [Local Recommendations](https://github.com/DrdotHouse2106/Lokal-Vorschlag-Jellyfin). Das Plugin lädt die Liste täglich und zeigt die Welten in Apps wie Quallenkino persönlich sortiert an. Die Jellyfin-Bibliothek wird dabei nicht verändert.

**Adresse für das Plugin** (Standard ab LocalRecs 12.12.0, Einstellung „Welten-Liste“):

```
https://raw.githubusercontent.com/DrdotHouse2106/Jellyfin-Welten/main/welten.json
```

## Dateien

| Datei | Inhalt | Bearbeiten? |
|---|---|---|
| [`regeln.json`](regeln.json) | Regeln pro Welt, TMDB-Quellen, **von Hand ergänzte Titel und Ausschlüsse** | **Ja** – hier wird gepflegt |
| [`welten.json`](welten.json) | Fertige Liste für das Plugin | Nein – wird automatisch erzeugt |
| [`scripts/aktualisieren.py`](scripts/aktualisieren.py) | Erzeugt `welten.json` aus `regeln.json` und TMDB | – |
| [`logos/`](logos/) | Selbst gestaltete Logos für Welten ohne passendes Marken-Logo (Bud Spencer & Terence Hill, Horror-Klassiker), erzeugt mit [`make_logos.py`](logos/make_logos.py) aus OFL-Schriften – siehe [`LIZENZ-Schriften.txt`](logos/LIZENZ-Schriften.txt) | bei Bedarf neu erzeugen |
| [`icons/`](icons/) | **Profilbild-Figuren** (rund 100, nach Kategorien) mit Katalog [`icons.json`](icons/icons.json) und Farbpalette – Standard für „Profilbild wählen“ in LocalRecs ab 12.22.0. Figuren von [OpenMoji](https://openmoji.org/) und eigene Zeichnungen, CC BY-SA 4.0 – siehe [`icons/LIZENZ.md`](icons/LIZENZ.md) | Ja – Figuren ergänzen, Eintrag in `icons.json` |

**Von Hand gepflegte Einträge gehen nie verloren:** Sie stehen in `regeln.json`, und das Skript liest diese Datei nur. Außerdem bleibt jeder Titel, der einmal in `welten.json` steht, dort – auch wenn er bei TMDB später unter die Stimmen-Schwelle rutscht. Entfernt wird ein Titel nur über einen Eintrag unter `ausschluss`.

## Automatische Aktualisierung

Die GitHub Action [`aktualisieren.yml`](.github/workflows/aktualisieren.yml) läuft jeden Montag, nach jeder Änderung an `regeln.json` und auf Knopfdruck (**Actions → Welten aktualisieren → Run workflow**). Sie fragt TMDB nach neuen Titeln (auch angekündigten) und committet `welten.json`, wenn sich etwas geändert hat.

Dafür braucht das Repository einen **TMDB-API-Schlüssel** als Secret: **Settings → Secrets and variables → Actions → New repository secret**, Name `TMDB_API_KEY`, Wert = API-Schlüssel (v3) oder Lese-Token (v4) von [themoviedb.org](https://www.themoviedb.org/settings/api). Ohne Secret übernimmt die Action nur Änderungen aus `regeln.json`.

## regeln.json

```json
{
  "welten": [
    {
      "name": "Pixar",
      "studios": ["Pixar"],
      "sammlungen": ["Toy Story", "Cars"],
      "tmdb": {
        "firmen": [ { "id": 3, "min_stimmen": 50 } ],
        "serien_firmen": [],
        "sammlungen": [10194],
        "ausschluss_muster": ["(?i)making[- ]of"]
      },
      "titel": [ { "tmdb": "1234", "typ": "film", "name": "Von Hand ergänzt" } ],
      "ausschluss": [ { "tmdb": "920", "typ": "film", "name": "Cars gehört woanders hin" }, { "sammlung": "Indiana Jones" } ]
    }
  ]
}
```

| Feld | Bedeutung |
|---|---|
| `logo` | Logo oder Liste von Logos in Reihenfolge – das erste, das klappt, wird verwendet: `fanart:collection/{TMDB-Sammlung}`, `fanart:movie/{TMDB-ID}` oder `fanart:tv/{TVDB-ID}` (Logos von fanart.tv, braucht einen fanart.tv-Schlüssel in den Plugin-Einstellungen), ein Link `https://…` (z. B. TMDB-Firmenlogo) oder ein Pfad relativ zu `welten.json`. Das Plugin lädt das Bild, speichert es zwischen und liefert es an Apps aus. Marken-Logos werden bewusst nicht als Datei hier abgelegt. |
| `trailer` | Optional: Titel, dessen lokaler Trailer (z. B. von Trailarr) im Hintergrund der Welt läuft – TMDB-ID (`"trailer": 671`) oder `{ "imdb": "tt…", "typ": "film" }`. Ohne Angabe nimmt das Plugin (ab 12.16.0) den zuletzt hinzugefügten Titel der Welt mit lokalem Trailer. |
| `aliase` | Frühere IDs der Welt (z. B. `harry-potter` nach der Umbenennung in „Wizarding World“) – Apps und Einstellungen, die die alte ID verwenden, funktionieren weiter. |
| `name` | Anzeigename; die ID im Plugin entsteht daraus (klein, Umlaute als ae/oe/ue/ss, Sonderzeichen als `-`) oder aus einem eigenen Feld `id`. |
| `studios`, `sammlungen` | Regeln, die das Plugin direkt in der Bibliothek anwendet (Teil des Studio- bzw. Sammlungsnamens). |
| `tmdb.firmen` | TMDB-Firmen-IDs; Filme mit mindestens `min_stimmen` Stimmen, angekündigte Filme immer (abschaltbar mit `"angekuendigte": false`). |
| `tmdb.serien_firmen` | TMDB-Firmen-IDs für Serien. |
| `tmdb.sammlungen` | TMDB-Sammlungs-IDs (z. B. 1241 = Harry Potter). |
| `tmdb.personen` | TMDB-Personen-IDs: alle Filme und Serien, in denen die Person mitspielt (ohne Dokus, Talk- und Reality-Shows und Auftritte als sie selbst); mit `ab_jahr` nur Titel ab diesem Jahr (z. B. Bud Spencer & Terence Hill ab 1967). |
| `tmdb.ausschluss_muster` | Reguläre Ausdrücke: neue TMDB-Titel mit passendem Namen werden nicht übernommen (z. B. Making-ofs). |
| `titel` | Von Hand ergänzte Titel (`tmdb` + `typ`, oder `imdb`, oder `tvdb`). |
| `ausschluss` | Titel, die nie dazugehören – auch wenn TMDB oder eine Regel sie liefert. Statt einer ID geht `"sammlung": "…"` (ganze Jellyfin-Sammlung). |

`typ` ist bei TMDB-IDs wichtig (`film` oder `serie`), weil sich die IDs von Filmen und Serien überschneiden. `name` dient nur der Lesbarkeit.

## Lokal ausführen

```bash
python3 -m unittest discover -s scripts           # Tests
TMDB_API_KEY=... python3 scripts/aktualisieren.py  # mit TMDB
python3 scripts/aktualisieren.py --ohne-tmdb       # nur regeln.json übernehmen
python3 scripts/aktualisieren.py --pruefen         # nichts schreiben
```

## Eigene Liste

Repository forken (oder `welten.json` kopieren), anpassen und im Plugin unter **Settings → Welten-Liste** die eigene Adresse eintragen.

## Quelle

Daten: [TMDB](https://www.themoviedb.org). Dieses Produkt nutzt die TMDB-API, ist aber nicht von TMDB unterstützt oder zertifiziert.

## Unterstützen

Die Entwicklung kostet Zeit und Geld (Server, Testgeräte, KI-Werkzeuge). Wenn dir das Projekt gefällt, freue ich mich über eine kleine Spende:

[![Spenden via PayPal](https://img.shields.io/badge/Spenden-PayPal-0070ba?logo=paypal&logoColor=white)](https://paypal.me/DrdotHouse)

### 🎮 Auch eine Zocker-Ader?

Dann ist vielleicht mein anderes Projekt genau das Richtige für dich: **[ZockerDB](https://zockerdb.de)** –
deine Spielesammlung an einem Platz. Spiele, Konsolen und Zubehör erfassen (auch per Barcode-Scan mit
dem Handy), bewerten und verwalten, mit Preisverlauf, Editionen und PAL/USK-Angaben. Direkt auf
[zockerdb.de](https://zockerdb.de) nutzen oder als [ZockerDB Basis](https://github.com/DrdotHouse2106/ZockerDBBasis) auf dem eigenen Server hosten.

## Profilbilder (icons/)

Der Katalog [`icons/icons.json`](icons/icons.json) ist der Standard für die Profilbilder im Plugin (Einstellung „Katalog der Profilbilder“):

```
https://raw.githubusercontent.com/DrdotHouse2106/Jellyfin-Welten/main/icons/icons.json
```

- `colors` – feste Farbpalette für den Hintergrund
- `categories` – Kategorien mit `id`, `name` und `icons`; jedes Icon mit `id`, `name` und `file` (Pfad relativ zu `icons.json`) oder `url`; optional `fit`: `contain` (Standard) oder `cover`
- Bilder: PNG mit transparentem Hintergrund, 256 × 256, höchstens 2 MB

**Eigene Zeichnungen:** Die Kategorien Superhelden, Märchen & Magie und Weltraum-Abenteuer zeichnet DrdotHouse2106 selbst, ebenfalls unter CC BY-SA 4.0. Die Quelle ist [`icons/quellen/zeichnen.py`](icons/quellen/zeichnen.py) und erzeugt SVGs in `icons/quellen/svg/`. Die Figuren erinnern nur an bekannte Welten. Es sind keine offiziellen Figuren, sie haben keine Logos und keine Namen.

**Neue Figur:** PNG in den passenden Ordner legen und in `icons.json` eintragen. Bitte nur Bilder verwenden, die frei weitergegeben werden dürfen, und die Quelle in [`icons/LIZENZ.md`](icons/LIZENZ.md) nennen.

