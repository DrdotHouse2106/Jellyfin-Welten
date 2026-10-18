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
        return {"parts": self.sammlungen.get(int(pfad.rsplit("/", 1)[1]), [])}


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

    def test_welt_id_wie_im_plugin(self):
        self.assertEqual(a.welt_id("Star Wars"), "star-wars")
        self.assertEqual(a.welt_id("Ärzte & Co."), "aerzte-co")

    def test_echte_dateien_sind_gueltig_und_stabil(self):
        root = Path(__file__).resolve().parent.parent
        regeln = json.loads((root / "regeln.json").read_text(encoding="utf-8"))
        welten = json.loads((root / "welten.json").read_text(encoding="utf-8"))
        dok, _ = a.erzeugen(regeln, welten, None)
        alt = {a.welt_id(w["name"]): len(w["titel"]) for w in welten["welten"]}
        for w in dok["welten"]:
            vorher = max([alt.get(a.welt_id(w["name"]), 0)] + [alt.get(x, 0) for x in w.get("aliase", [])])
            self.assertGreaterEqual(len(w["titel"]), vorher - sum(1 for x in w["ausschluss"] if x.get("tmdb")), w["name"])


if __name__ == "__main__":
    unittest.main()
