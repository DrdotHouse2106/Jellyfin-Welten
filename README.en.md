# Jellyfin-Welten

[![Buy me a coffee](https://img.shields.io/badge/☕_Buy_me_a_coffee-PayPal-0070ba?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/DrdotHouse)

Disney+-like "worlds" (Marvel, Star Wars, DC, Pixar, Disney, DreamWorks, Illumination, Wizarding World, Middle-earth, James Bond, Jurassic Park, Studio Ghibli) as a list for the Jellyfin plugin [Local Recommendations](https://github.com/DrdotHouse2106/Lokal-Vorschlag-Jellyfin). The plugin loads the list daily; the library is not changed.

Plugin URL (default since LocalRecs 12.12.0, setting "Welten-Liste"): `https://raw.githubusercontent.com/DrdotHouse2106/Jellyfin-Welten/main/welten.json`

- `regeln.json` – rules, TMDB sources, **manually added titles and exclusions** (edit this file).
- Each world may have a `logo` or a list of logos in order of preference (`fanart:collection/{id}` etc. via fanart.tv with a key in the plugin settings, https link, e.g. a TMDB company logo, or a path relative to `welten.json`) `aliase` (former IDs) and `trailer` (optional: the title whose local trailer plays behind the world, TMDB ID or `{ "imdb": …, "typ": … }`; otherwise plugin 12.16.0+ uses the most recently added title with a local trailer); brand logos are deliberately not stored as files here.
- `welten.json` – generated list for the plugin (do not edit).
- `scripts/aktualisieren.py` – builds `welten.json` from `regeln.json` and TMDB. Manual entries are never lost (they live in `regeln.json`, which the script only reads), and titles once in `welten.json` stay unless excluded.

The GitHub Action runs weekly, on changes to `regeln.json` and on demand. It needs a repository secret `TMDB_API_KEY` (TMDB v3 API key or v4 read token); without it only `regeln.json` changes are applied.

Data: [TMDB](https://www.themoviedb.org). This product uses the TMDB API but is not endorsed or certified by TMDB.

## Support the project

Development costs time and money (servers, test devices, AI tools). If you like the project, a small donation is very welcome:

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-0070ba?logo=paypal&logoColor=white)](https://paypal.me/DrdotHouse)
