# Jellyfin-Welten

Disney+-like "worlds" (Marvel, Star Wars, DC, Pixar, Disney, DreamWorks, Illumination, Harry Potter, Middle-earth, James Bond, Jurassic Park, Studio Ghibli) as a list for the Jellyfin plugin [Local Recommendations](https://github.com/DrdotHouse2106/Lokal-Vorschlag-Jellyfin). The plugin loads the list daily; the library is not changed.

Plugin URL (default since LocalRecs 12.12.0, setting "Welten-Liste"): `https://raw.githubusercontent.com/DrdotHouse2106/Jellyfin-Welten/main/welten.json`

- `regeln.json` – rules, TMDB sources, **manually added titles and exclusions** (edit this file).
- Each world may have a `logo` (https link, e.g. a TMDB company logo, or a path relative to `welten.json`); brand logos are deliberately not stored as files here.
- `welten.json` – generated list for the plugin (do not edit).
- `scripts/aktualisieren.py` – builds `welten.json` from `regeln.json` and TMDB. Manual entries are never lost (they live in `regeln.json`, which the script only reads), and titles once in `welten.json` stay unless excluded.

The GitHub Action runs weekly, on changes to `regeln.json` and on demand. It needs a repository secret `TMDB_API_KEY` (TMDB v3 API key or v4 read token); without it only `regeln.json` changes are applied.

Data: [TMDB](https://www.themoviedb.org). This product uses the TMDB API but is not endorsed or certified by TMDB.
