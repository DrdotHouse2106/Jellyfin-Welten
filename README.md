# Jellyfin-Welten

*[English version](README.en.md)*

„Welten“ wie bei Disney+ – Marvel, Star Wars, DC, Pixar, Disney, DreamWorks, Illumination, Harry Potter, Mittelerde, James Bond, Jurassic Park, Studio Ghibli – als Liste für das Jellyfin-Plugin [Local Recommendations](https://github.com/DrdotHouse2106/Lokal-Vorschlag-Jellyfin). Das Plugin lädt die Liste täglich und zeigt die Welten in Apps wie Quallenkino persönlich sortiert an. Die Jellyfin-Bibliothek wird dabei nicht verändert.

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
| `logo` | Link auf ein Logo (`https://…`, z. B. ein TMDB-Firmenlogo von image.tmdb.org) oder ein Pfad relativ zu `welten.json` (für selbst erstellte Logos). Das Plugin lädt das Bild, speichert es zwischen und liefert es an Apps aus. Marken-Logos werden bewusst nicht als Datei hier abgelegt. |
| `name` | Anzeigename; die ID im Plugin entsteht daraus (klein, Umlaute als ae/oe/ue/ss, Sonderzeichen als `-`) oder aus einem eigenen Feld `id`. |
| `studios`, `sammlungen` | Regeln, die das Plugin direkt in der Bibliothek anwendet (Teil des Studio- bzw. Sammlungsnamens). |
| `tmdb.firmen` | TMDB-Firmen-IDs; Filme mit mindestens `min_stimmen` Stimmen, angekündigte Filme immer (abschaltbar mit `"angekuendigte": false`). |
| `tmdb.serien_firmen` | TMDB-Firmen-IDs für Serien. |
| `tmdb.sammlungen` | TMDB-Sammlungs-IDs (z. B. 1241 = Harry Potter). |
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
