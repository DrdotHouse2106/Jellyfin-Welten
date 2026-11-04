"""Tests für aktualisieren.py (ohne Netz): python3 -m unittest discover -s scripts"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aktualisieren as a  # noqa: E402


class FakeTmdb:
    def __init__(self, filme=None, serien=None, sammlungen=None):
        self.filme, self.serien, self.sammlungen = filme or {}, serien or {}, sammlungen or {}

    def discover(self, art, **params):
        quelle = self.filme if art == "movie" else self.serien
        if "primary_release_date.gte" in params:
            return [f for f in quelle.get(params["with_companies"], []) if f.get("release_date", "") >= params["primary_release_date.gte"]]
        return [f for f in quelle.get(params["with_companies"], []) if f.get("vote_count", 0) >= params.get("vote_count.gte", 0)]

    def get(self, pfad, **params):
        if pfad.endswith("/combined_credits"):
            return {"cast": PERSON_CAST}
        return {"parts": self.sammlungen.get(int(pfad.rsplit("/", 1)[1]), [])}


PERSON_CAST = [
    {"id": 11829, "media_type": "movie", "title": "Vier Fäuste für ein Halleluja", "release_date": "1971-10-21", "genre_ids": [37, 35]},
    {"id": 1000, "media_type": "movie", "title": "Früher Film", "release_date": "1959-01-01", "genre_ids": [18]},
    {"id": 1001, "media_type": "movie", "title": "Doku", "release_date": "2010-01-01", "genre_ids": [99]},
    {"id": 1002, "media_type": "tv", "name": "Talkshow", "first_air_date": "2000-01-01", "genre_ids": [10767]},
    {"id": 1003, "media_type": "movie", "title": "Gastauftritt", "release_date": "2015-01-01", "genre_ids": [35], "character": "Himself"},
    {"id": 21220, "media_type": "tv", "name": "Don Matteo", "first_air_date": "2000-01-07", "genre_ids": [80, 18]},
    {"id": 1004, "media_type": "movie", "title": "Angekündigt", "release_date": "", "genre_ids": []}]


REGELN = {"welten": [{
    "name": "Pixar", "logo": "https://image.tmdb.org/t/p/w500/pixar.png", "studios": ["Pixar"], "sammlungen": ["Toy Story"],
    "tmdb": {"firmen": [{"id": 3, "min_stimmen": 50}], "sammlungen": [10194], "ausschluss_muster": ["(?i)making[- ]of"]},
    "titel": [{"tmdb": "999", "typ": "film", "name": "Von Hand ergänzt"}],
    "ausschluss": [{"tmdb": "920", "typ": "film", "name": "Cars"}, {"sammlung": "Indiana Jones"}]}]}

ALT = {"welten": [{"name": "Pixar", "titel": [
    {"tmdb": "862", "typ": "film", "name": "Toy Story"},
    {"tmdb": "920", "typ": "film", "name": "Cars"},
    {"tmdb": "1", "typ": "film", "name": "Alter Titel, bei TMDB inzwischen unter der Schwelle"}]}]}

TMDB = FakeTmdb(
    filme={3: [
        {"id": 862, "title": "Toy Story", "vote_count": 9000, "release_date": "1995-11-22"},
        {"id": 2062, "title": "Ratatouille", "vote_count": 8000, "release_date": "2007-06-28"},
        {"id": 5, "title": "Making-of Ratatouille", "vote_count": 60, "release_date": "2007-07-01"},
        {"id": 6, "title": "Unwichtig", "vote_count": 3, "release_date": "2001-01-01"},
        {"id": 7, "title": "Angekündigt", "vote_count": 0, "release_date": "2099-01-01"},
        {"id": 920, "title": "Cars", "vote_count": 7000, "release_date": "2006-06-08"}]},
    sammlungen={10194: [{"id": 863, "title": "Toy Story 2", "release_date": "1999-10-30"}]})


class Tests(unittest.TestCase):
    def setUp(self):
        self.dok, self.bericht = a.erzeugen(REGELN, ALT, TMDB, heute="2026-10-18")
        self.ids = [t["tmdb"] for t in self.dok["welten"][0]["titel"]]

    def test_bisherige_und_hand_eintraege_bleiben(self):
        self.assertIn("1", self.ids, "einmal drin, bleibt drin")
        self.assertIn("999", self.ids, "von Hand ergänzt")

    def test_neue_tmdb_titel_kommen_dazu(self):
        self.assertIn("2062", self.ids)
        self.assertIn("863", self.ids, "aus der TMDB-Sammlung")
        self.assertIn("7", self.ids, "angekündigt, ohne Mindeststimmen")

    def test_ausschluss_muster_und_schwelle(self):
        self.assertNotIn("920", self.ids, "Ausschluss entfernt auch bisherige Einträge")
        self.assertNotIn("5", self.ids, "Making-of per Muster gefiltert")
        self.assertNotIn("6", self.ids, "unter der Mindestzahl an Stimmen")

    def test_keine_dubletten_und_reihenfolge(self):
        self.assertEqual(len(self.ids), len(set(self.ids)))
        self.assertEqual(self.ids[:2], ["862", "1"], "bisherige Reihenfolge bleibt")

    def test_bericht(self):
        name, anzahl, neu, entfernt = self.bericht[0]
        self.assertEqual(name, "Pixar")
        self.assertEqual([e["tmdb"] for e in entfernt], ["920"])
        self.assertEqual(anzahl, len(self.ids))

    def test_ausschluesse_und_regeln_landen_in_welten_json(self):
        welt = self.dok["welten"][0]
        self.assertEqual(welt["studios"], ["Pixar"])
        self.assertEqual(welt["logo"], "https://image.tmdb.org/t/p/w500/pixar.png")
        self.assertIn({"sammlung": "Indiana Jones"}, welt["ausschluss"])

    def test_ohne_tmdb_aendert_sich_nur_durch_regeln(self):
        dok, _ = a.erzeugen(REGELN, ALT, None)
        self.assertEqual([t["tmdb"] for t in dok["welten"][0]["titel"]], ["862", "1", "999"])

    def test_umbenennung_verliert_keine_titel(self):
        regeln = {"welten": [{"name": "Wizarding World", "aliase": ["harry-potter"], "titel": []}]}
        alt = {"welten": [{"name": "Harry Potter", "titel": [{"tmdb": "671", "typ": "film"}]}]}
        dok, _ = a.erzeugen(regeln, alt, None)
        self.assertEqual([t["tmdb"] for t in dok["welten"][0]["titel"]], ["671"])
        self.assertEqual(dok["welten"][0]["aliase"], ["harry-potter"])

    def test_trailer_wird_uebernommen(self):
        regeln = {"welten": [{"name": "Wizarding World", "trailer": 671, "titel": [{"tmdb": "671", "typ": "film"}]}]}
        dok, _ = a.erzeugen(regeln, {"welten": []}, None)
        self.assertEqual(dok["welten"][0]["trailer"], 671)

    def test_personen_mit_filtern(self):
        regeln = {"welten": [{"name": "Bud Spencer & Terence Hill", "tmdb": {"personen": [{"id": 15140, "ab_jahr": 1967}]}, "titel": []}]}
        dok, _ = a.erzeugen(regeln, {"welten": []}, FakeTmdb(), heute="2026-10-18")
        titel = {(t["tmdb"], t["typ"]) for t in dok["welten"][0]["titel"]}
        self.assertEqual(titel, {("11829", "film"), ("21220", "serie"), ("1004", "film")})

    def test_welt_id_wie_im_plugin(self):
        self.assertEqual(a.welt_id("Star Wars"), "star-wars")
        self.assertEqual(a.welt_id("Ärzte & Co."), "aerzte-co")

    def test_echte_dateien_sind_gueltig_und_stabil(self):
        root = Path(__file__).resolve().parent.parent
        regeln = json.loads((root / "regeln.json").read_text(encoding="utf-8"))
        welten = json.loads((root / "welten.json").read_text(encoding="utf-8"))
        dok, _ = a.erzeugen(regeln, welten, None)
        # Platzhalter („Untitled …“) fallen absichtlich weg
        alt = {a.welt_id(w["name"]): sum(1 for t in w["titel"] if not a.ist_platzhalter(t)) for w in welten["welten"]}
        for w in dok["welten"]:
            vorher = max([alt.get(a.welt_id(w["name"]), 0)] + [alt.get(x, 0) for x in w.get("aliase", [])])
            self.assertGreaterEqual(len(w["titel"]), vorher - sum(1 for x in w["ausschluss"] if x.get("tmdb")), w["name"])


class ChronologieTest(unittest.TestCase):
    def test_chronologie_wird_uebernommen(self):
        regeln = {"welten": [{"name": "Star Trek", "titel": [{"tmdb": "314", "typ": "serie", "name": "Enterprise"}],
                              "chronologie": [{"abschnitt": "Kelvin-Zeitlinie"},
                                              {"tmdb": "67198", "typ": "serie", "label": "2256–2258", "staffeln": [1, 2]}]}]}
        dok, _ = a.erzeugen(regeln, {"welten": []}, tmdb=None, heute="2026-10-27")
        self.assertEqual(dok["welten"][0]["chronologie"], regeln["welten"][0]["chronologie"])

    def test_ohne_chronologie_kein_feld(self):
        dok, _ = a.erzeugen({"welten": [{"name": "Pixar", "studios": ["Pixar"]}]}, {"welten": []}, tmdb=None, heute="2026-10-27")
        self.assertNotIn("chronologie", dok["welten"][0])

    def test_pruefen_formfehler(self):
        titel = [{"tmdb": "67198", "typ": "serie"}, {"tmdb": "13475", "typ": "film"}]
        for falsch in ([{"label": "2151"}],
                       [{"abschnitt": ""}],
                       [{"tmdb": "67198", "label": "x"}],
                       [{"tmdb": "13475", "typ": "film", "staffeln": [1]}],
                       [{"tmdb": "67198", "typ": "serie", "staffeln": [0]}],
                       [{"tmdb": "67198", "typ": "serie", "staffeln": "1"}],
                       [{"tmdb": "67198", "typ": "serie", "staffeln": []}]):
            with self.assertRaises(ValueError, msg=str(falsch)):
                a.chronologie_pruefen("Star Trek", falsch, titel)

    def test_pruefen_warnt_bei_fremdem_titel_und_staffeln(self):
        class FakeTmdb:
            def get(self, pfad, **params):
                return {"number_of_seasons": 5} if pfad == "/tv/67198" else {}

        titel = [{"tmdb": "67198", "typ": "serie"}]
        ok = [{"abschnitt": "Hauptzeitlinie"}, {"tmdb": "67198", "typ": "serie", "label": "3188", "staffeln": [3, 4, 5]}]
        self.assertEqual(a.chronologie_pruefen("Star Trek", ok, titel, FakeTmdb()), [])
        warn = a.chronologie_pruefen("Star Trek", [{"tmdb": "999", "typ": "film", "label": "2400"},
                                                   {"tmdb": "67198", "typ": "serie", "staffeln": [6]}], titel, FakeTmdb())
        self.assertEqual(len(warn), 2)
        self.assertIn("gehört nicht zur Welt", warn[0])
        self.assertIn("Staffel 6", warn[1])


class SucheTest(unittest.TestCase):
    class FakeTmdb:
        def __init__(self):
            self.aufrufe = []

        def get(self, pfad, **params):
            self.aufrufe.append((pfad, params))
            if pfad == "/search/movie" and params["query"] == "Psycho":
                if params.get("primary_release_year") == 1960:
                    return {"results": [{"id": 539, "title": "Psycho", "release_date": "1960-06-22"}]}
                return {"results": [{"id": 11252, "title": "Psycho", "release_date": "1998-12-04"}]}
            if pfad == "/search/tv" and params["query"] == "Smallville":
                return {"results": [{"id": 4604, "name": "Smallville", "first_air_date": "2001-10-16"}]}
            if pfad == "/search/collection":
                treffer = {"Halloween": [{"id": 999, "name": "Halloween (Rob Zombie) Collection"}, {"id": 91361, "name": "Halloween"}]}
                return {"results": treffer.get(params["query"], [])}
            if pfad == "/collection/91361":
                return {"parts": [{"id": 948, "title": "Halloween", "release_date": "1978-10-24"},
                                  {"id": 1, "title": "Untitled Halloween Sequel", "release_date": ""}]}
            if pfad == "/search/company":
                return {"results": [{"id": 3166, "name": "Walt Disney Productions"}]}
            if pfad.startswith("/discover/"):
                return {"results": [{"id": 12, "title": "Schneewittchen und die sieben Zwerge", "release_date": "1937-12-21"}], "total_pages": 1}
            return {"results": []}

        def discover(self, art, **params):
            return self.get("/discover/" + art, **params)["results"]

    def test_namenssuche_titel_sammlung_firma(self):
        tmdb = self.FakeTmdb()
        meldungen = []
        quelle = {"suche": [{"titel": "Psycho", "jahr": 1960, "typ": "film"}, {"titel": "Smallville", "jahr": 2001, "typ": "serie"},
                            {"titel": "Gibt es nicht", "jahr": 1999, "typ": "film"}],
                  "sammlungen_suche": ["Halloween", "Unbekannt"],
                  "firmen_suche": [{"name": "Walt Disney Productions", "min_stimmen": 100, "angekuendigte": False}]}
        titel = a.tmdb_titel(tmdb, quelle, "2026-11-04", meldungen)
        ids = {(t["tmdb"], t["typ"]) for t in titel}
        self.assertIn(("539", "film"), ids, "Psycho von 1960, nicht das Remake")
        self.assertNotIn(("11252", "film"), ids)
        self.assertIn(("4604", "serie"), ids)
        self.assertIn(("948", "film"), ids, "genauer Sammlungsname vor erstem Treffer")
        self.assertIn(("12", "film"), ids, "Firma über den Namen")
        self.assertTrue(any("Titel nicht gefunden: Gibt es nicht" in m for m in meldungen))
        self.assertTrue(any("Sammlung nicht gefunden: Unbekannt" in m for m in meldungen))

    def test_platzhalter_fallen_weg_auch_aus_alten_eintraegen(self):
        regel = {"name": "X"}
        alt = [{"tmdb": "1", "typ": "film", "name": "Untitled X-Men Film"}, {"tmdb": "2", "typ": "film", "name": "X-Men"}]
        neu = [{"tmdb": "3", "typ": "film", "name": "Untitled Sequel", "datum": "2028-01-01"}]
        titel, neu_hinzu = a.welt_zusammenfuehren(regel, alt, neu)
        self.assertEqual([t["tmdb"] for t in titel], ["2"])
        self.assertEqual(neu_hinzu, [])


class AbschnitteTest(unittest.TestCase):
    TITEL = [
        {"tmdb": "1", "typ": "film", "name": "Bambi", "jahr": 1942, "genres": [16, 10751]},
        {"tmdb": "2", "typ": "film", "name": "Fluch der Karibik", "jahr": 2003, "genres": [12, 14, 28]},
        {"tmdb": "3", "typ": "film", "name": "Der König der Löwen", "jahr": 2019, "genres": [12, 18]},
        {"tmdb": "4", "typ": "film", "name": "Santa Clause", "jahr": 1994, "genres": [35, 10751]},
        {"tmdb": "5", "typ": "serie", "name": "Andor", "jahr": 2022, "genres": [10765]},
        {"tmdb": "6", "typ": "film", "name": "Halloween", "jahr": 1978, "genres": [27], "reihe": 91361, "reihe_name": "Halloween Collection"},
        {"tmdb": "7", "typ": "film", "name": "Halloween II", "jahr": 1981, "genres": [27], "reihe": 91361, "reihe_name": "Halloween Collection"},
        {"tmdb": "8", "typ": "film", "name": "Freitag der 13.", "jahr": 1980, "genres": [27], "reihe": 9735, "reihe_name": "Friday the 13th Collection"},
        {"tmdb": "9", "typ": "film", "name": "Psycho", "jahr": 1960, "genres": [27]},
    ]

    def titel(self):
        return [dict(t) for t in self.TITEL]

    def test_erste_passende_regel_gewinnt_rest_faengt_alles(self):
        titel = self.titel()[:5]
        regeln = [{"name": "Animation", "typ": "film", "genres": [16]},
                  {"name": "Realverfilmungen", "tmdb": ["3"], "min_stimmen_fehlend": 300},
                  {"name": "Abenteuer und Fantasy", "typ": "film", "genres": [12, 14, 878]},
                  {"name": "Serien", "typ": "serie"},
                  {"name": "Familienfilme und Sonstiges"}]
        abschnitte = a.abschnitte_zuordnen(regeln, titel)
        zuordnung = {t["name"]: t["abschnitt"] for t in titel}
        self.assertEqual(zuordnung["Bambi"], "Animation")
        self.assertEqual(zuordnung["Der König der Löwen"], "Realverfilmungen", "Liste vor Genre")
        self.assertEqual(zuordnung["Fluch der Karibik"], "Abenteuer und Fantasy")
        self.assertEqual(zuordnung["Andor"], "Serien")
        self.assertEqual(zuordnung["Santa Clause"], "Familienfilme und Sonstiges")
        self.assertEqual([x["name"] for x in abschnitte], ["Animation", "Realverfilmungen", "Abenteuer und Fantasy", "Serien", "Familienfilme und Sonstiges"])
        self.assertEqual(abschnitte[1]["min_stimmen_fehlend"], 300)

    def test_je_reihe_und_leere_abschnitte_fallen_weg(self):
        titel = self.titel()[5:]
        abschnitte = a.abschnitte_zuordnen([{"name": "Reihen", "je_reihe": True}, {"name": "Leer", "typ": "serie"}, {"name": "Einzelne Klassiker"}], titel)
        self.assertEqual([x["name"] for x in abschnitte], ["Halloween", "Einzelne Klassiker"],
                         "Reihen ab zwei Titeln, ohne „Collection“; einzelne Filme einer Reihe zu den Klassikern")
        self.assertEqual({t["name"]: t["abschnitt"] for t in titel}["Freitag der 13."], "Einzelne Klassiker")
        self.assertEqual({t["name"]: t["abschnitt"] for t in titel}["Psycho"], "Einzelne Klassiker")

    def test_zuerst_prueft_vorher_ohne_reihenfolge_zu_aendern(self):
        titel = [{"tmdb": "3", "typ": "film", "name": "Der König der Löwen", "jahr": 2019, "genres": [12, 16]},
                 {"tmdb": "1", "typ": "film", "name": "Bambi", "jahr": 1942, "genres": [16]}]
        abschnitte = a.abschnitte_zuordnen([{"name": "Animation", "genres": [16]}, {"name": "Realverfilmungen", "tmdb": ["3"], "zuerst": True}], titel)
        self.assertEqual([x["name"] for x in abschnitte], ["Animation", "Realverfilmungen"])
        self.assertEqual([t["abschnitt"] for t in titel], ["Realverfilmungen", "Animation"])

    def test_name_muster_und_jahre(self):
        titel = [{"tmdb": "10", "typ": "film", "name": "Batman", "jahr": 1989, "genres": [28]},
                 {"tmdb": "11", "typ": "film", "name": "The Batman", "jahr": 2022, "genres": [28]},
                 {"tmdb": "12", "typ": "film", "name": "Batman: Year One", "jahr": 2011, "genres": [16]}]
        a.abschnitte_zuordnen([{"name": "Animation", "genres": [16]}, {"name": "Klassisch", "typ": "film", "bis_jahr": 2012},
                               {"name": "DCU", "typ": "film", "ab_jahr": 2013, "name_muster": "(?i)batman"}], titel)
        self.assertEqual([t["abschnitt"] for t in titel], ["Klassisch", "DCU", "Animation"])

    def test_ohne_tmdb_bleibt_die_bisherige_zuordnung(self):
        regeln = {"welten": [{"name": "Disney", "titel": [{"tmdb": "1", "typ": "film"}], "abschnitte": [{"name": "Animation", "titel_suche": [{"titel": "Bambi", "jahr": 1942, "typ": "film"}]}]}]}
        alt = {"welten": [{"name": "Disney", "abschnitte": [{"name": "Animation"}], "titel": [{"tmdb": "1", "typ": "film", "name": "Bambi", "jahr": 1942, "abschnitt": "Animation"}]}]}
        dok, _ = a.erzeugen(regeln, alt, tmdb=None, heute="2026-11-05")
        self.assertEqual(dok["welten"][0]["abschnitte"], [{"name": "Animation"}])
        self.assertEqual(dok["welten"][0]["titel"][0]["abschnitt"], "Animation")


if __name__ == "__main__":
    unittest.main()
