#!/usr/bin/env python3
"""Aktualisiert welten.json aus regeln.json und TMDB.

Grundsätze:
- regeln.json wird nur gelesen, nie geschrieben. Von Hand ergänzte Titel ("titel") und
  Ausschlüsse ("ausschluss") stehen dort und gehen daher nie verloren.
- Was einmal in welten.json steht, bleibt drin (TMDB-Stimmen schwanken). Entfernt wird ein
  Titel nur über einen Eintrag unter "ausschluss" in regeln.json.
- Neue Titel kommen aus TMDB: Firmen (mit Mindestzahl an Stimmen, angekündigte Filme ohne
  Mindestzahl), Serien von Firmen und TMDB-Sammlungen. "ausschluss_muster" filtert neue
  Titel nach Namen (z. B. Making-ofs).

Aufruf:
    TMDB_API_KEY=... python3 scripts/aktualisieren.py          # mit TMDB
    python3 scripts/aktualisieren.py --ohne-tmdb               # nur Regeln/Hand-Einträge übernehmen
    python3 scripts/aktualisieren.py --pruefen                 # nichts schreiben, Änderungen zeigen

Daten: TMDB (https://www.themoviedb.org). Dieses Produkt nutzt die TMDB-API, ist aber nicht
von TMDB unterstützt oder zertifiziert.
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGELN = ROOT / "regeln.json"
WELTEN = ROOT / "welten.json"
API = "https://api.themoviedb.org/3"
MAX_SEITEN = 25
OHNE_GENRES = {99, 10763, 10764, 10767}  # Dokumentation, Nachrichten, Reality, Talk
SELBST = re.compile(r"(?i)\b(himself|herself|self|sich selbst|se stesso)\b")

BESCHREIBUNG = (
    "Welten für das Jellyfin-Plugin Local Recommendations (LocalRecs). Diese Datei wird von "
    "scripts/aktualisieren.py aus regeln.json und TMDB erzeugt – Änderungen bitte in regeln.json. "
    "Ein Titel gehört zu einer Welt, wenn ein Studio oder der Name einer Jellyfin-Sammlung passt "
    "(Teil des Namens genügt) oder wenn er unter \"titel\" steht; Titel unter \"ausschluss\" gehören nie dazu. "
    "Die Titel-Listen sind vollständig aus TMDB (auch angekündigte Titel) und sagen nichts über eine "
    "bestimmte Bibliothek aus. \"chronologie\" (optional) ist die Reihenfolge nach Handlungszeit: Abschnitte "
    "({\"abschnitt\"}) und Titel ({\"tmdb\", \"typ\", \"label\", \"staffeln\"}), dieselbe Serie auch mehrfach mit "
    "verschiedenen Staffeln."
)
QUELLE = "Daten: TMDB (https://www.themoviedb.org). Dieses Produkt nutzt die TMDB-API, ist aber nicht von TMDB unterstützt oder zertifiziert."


def welt_id(name):
    """ID einer Welt wie im Plugin: klein, Umlaute ersetzt, Sonderzeichen als Bindestrich."""
    ersatz = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    ergebnis = ""
    for zeichen in (name or "").lower():
        if zeichen in ersatz:
            ergebnis += ersatz[zeichen]
        elif zeichen.isascii() and zeichen.isalnum():
            ergebnis += zeichen
        elif ergebnis and not ergebnis.endswith("-"):
            ergebnis += "-"
    return ergebnis.strip("-")


def schluessel(eintrag):
    """Eindeutiger Schlüssel eines Titels: TMDB-ID + Typ, sonst IMDb/TVDB."""
    if eintrag.get("tmdb"):
        return ("tmdb", str(eintrag["tmdb"]), eintrag.get("typ") or "")
    if eintrag.get("imdb"):
        return ("imdb", str(eintrag["imdb"]).lower(), "")
    if eintrag.get("tvdb"):
        return ("tvdb", str(eintrag["tvdb"]), "")
    return None


def ist_ausgeschlossen(eintrag, ausschluss):
    """Prüft, ob ein Titel unter den Ausschlüssen steht (ID-Vergleich, Typ falls angegeben)."""
    for a in ausschluss:
        if a.get("sammlung") and not (a.get("tmdb") or a.get("imdb") or a.get("tvdb")):
            continue
        typ_passt = not a.get("typ") or not eintrag.get("typ") or a["typ"] == eintrag["typ"]
        if a.get("tmdb") and eintrag.get("tmdb") and str(a["tmdb"]) == str(eintrag["tmdb"]) and typ_passt:
            return True
        if a.get("imdb") and eintrag.get("imdb") and str(a["imdb"]).lower() == str(eintrag["imdb"]).lower():
            return True
        if a.get("tvdb") and eintrag.get("tvdb") and str(a["tvdb"]) == str(eintrag["tvdb"]):
            return True
    return False


class Tmdb:
    """Kleiner TMDB-Client (v3-Schlüssel oder v4-Lesetoken)."""

    def __init__(self, key):
        self.key = key

    def get(self, pfad, **params):
        params.setdefault("language", "de-DE")
        headers = {"Accept": "application/json", "User-Agent": "jellyfin-welten"}
        if len(self.key) > 40:
            headers["Authorization"] = "Bearer " + self.key
        else:
            params["api_key"] = self.key
        url = API + pfad + "?" + urllib.parse.urlencode(params)
        for versuch in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as antwort:
                    return json.load(antwort)
            except urllib.error.HTTPError as fehler:
                if fehler.code == 429 and versuch < 3:
                    time.sleep(2 * (versuch + 1))
                    continue
                raise
        return {}

    def discover(self, art, **params):
        ergebnisse = []
        for seite in range(1, MAX_SEITEN + 1):
            daten = self.get("/discover/" + art, page=seite, **params)
            ergebnisse.extend(daten.get("results", []))
            if seite >= daten.get("total_pages", 0):
                break
        return ergebnisse


def tmdb_titel(tmdb, quelle, heute):
    """Sammelt die Titel einer Welt aus TMDB: [{tmdb, typ, name, datum}]."""
    gefunden = []
    for firma in quelle.get("firmen", []):
        filme = tmdb.discover("movie", with_companies=firma["id"], sort_by="popularity.desc",
                              **{"vote_count.gte": firma.get("min_stimmen", 0)})
        if firma.get("angekuendigte", True):
            filme += tmdb.discover("movie", with_companies=firma["id"], sort_by="primary_release_date.asc",
                                   **{"primary_release_date.gte": heute})
        gefunden += [{"tmdb": str(f["id"]), "typ": "film", "name": f.get("title") or f.get("original_title"),
                      "datum": f.get("release_date") or ""} for f in filme]
    for firma in quelle.get("serien_firmen", []):
        serien = tmdb.discover("tv", with_companies=firma["id"], sort_by="popularity.desc",
                               **{"vote_count.gte": firma.get("min_stimmen", 0)})
        gefunden += [{"tmdb": str(s["id"]), "typ": "serie", "name": s.get("name") or s.get("original_name"),
                      "datum": s.get("first_air_date") or ""} for s in serien]
    for person in quelle.get("personen", []):
        # Filme und Serien einer Person (als Darsteller), ohne Dokus/Talk-/Reality-Shows und Auftritte als sie selbst
        cast = tmdb.get("/person/" + str(person["id"]) + "/combined_credits").get("cast", [])
        for c in cast:
            datum = c.get("release_date") or c.get("first_air_date") or ""
            if person.get("ab_jahr") and datum and datum[:4] < str(person["ab_jahr"]):
                continue
            if set(c.get("genre_ids") or []) & OHNE_GENRES:
                continue
            if SELBST.search(c.get("character") or ""):
                continue
            serie = c.get("media_type") == "tv"
            gefunden.append({"tmdb": str(c["id"]), "typ": "serie" if serie else "film",
                             "name": (c.get("name") if serie else c.get("title")) or c.get("original_title") or c.get("original_name"),
                             "datum": datum})
    for sammlung in quelle.get("sammlungen", []):
        teile = tmdb.get("/collection/" + str(sammlung)).get("parts", [])
        gefunden += [{"tmdb": str(t["id"]), "typ": "film", "name": t.get("title") or t.get("original_title"),
                      "datum": t.get("release_date") or ""} for t in teile]
    return gefunden


def welt_zusammenfuehren(regel, alt, neu):
    """Neue Titelliste einer Welt: bisherige + Hand-Einträge + neue TMDB-Titel, ohne Ausschlüsse."""
    ausschluss = regel.get("ausschluss", [])
    muster = [re.compile(m) for m in regel.get("tmdb", {}).get("ausschluss_muster", [])]
    ergebnis, gesehen = [], set()

    def hinzu(eintrag, filtern):
        k = schluessel(eintrag)
        if k is None or k in gesehen or ist_ausgeschlossen(eintrag, ausschluss):
            return False
        if filtern and any(m.search(eintrag.get("name") or "") for m in muster):
            return False
        gesehen.add(k)
        ergebnis.append({f: eintrag[f] for f in ("tmdb", "imdb", "tvdb", "typ", "name") if eintrag.get(f)})
        return True

    for eintrag in alt:                      # 1. was schon drin ist, bleibt (Reihenfolge bleibt)
        hinzu(eintrag, False)
    for eintrag in regel.get("titel", []):   # 2. von Hand ergänzte Titel
        hinzu(eintrag, False)
    neu_hinzu = []
    for eintrag in sorted(neu, key=lambda e: e.get("datum") or "9999"):  # 3. neue TMDB-Titel
        if hinzu(eintrag, True):
            neu_hinzu.append(eintrag)
    return ergebnis, neu_hinzu


def chronologie_pruefen(name, chronologie, titel, tmdb=None):
    """Prüft die Chronologie einer Welt.

    Formfehler (kein Abschnitt und keine ID, falscher Typ, ungültige Staffeln) brechen mit ValueError ab.
    Inhaltliche Auffälligkeiten kommen als Warnungen zurück: Titel, die nicht zur Welt gehören (das Plugin
    würde sie nie anzeigen), und – mit TMDB – Staffeln, die es bei der Serie nicht gibt.
    """
    if not isinstance(chronologie, list):
        raise ValueError(f"{name}: chronologie muss eine Liste sein")
    bekannt = {schluessel(e) for e in titel}
    warnungen, staffelzahl = [], {}
    for nr, eintrag in enumerate(chronologie, 1):
        ort = f"{name}, chronologie Eintrag {nr}"
        if not isinstance(eintrag, dict):
            raise ValueError(f"{ort}: Objekt erwartet")
        if "abschnitt" in eintrag:
            if not str(eintrag["abschnitt"]).strip() or schluessel(eintrag):
                raise ValueError(f"{ort}: Abschnitt braucht einen Namen und keine ID")
            continue
        if not schluessel(eintrag):
            raise ValueError(f"{ort}: weder abschnitt noch tmdb/imdb/tvdb")
        if eintrag.get("typ") not in ("film", "serie"):
            raise ValueError(f"{ort}: typ muss film oder serie sein")
        staffeln = eintrag.get("staffeln")
        if staffeln is not None:
            if eintrag["typ"] != "serie":
                raise ValueError(f"{ort}: staffeln nur bei Serien")
            if not isinstance(staffeln, list) or not staffeln or any(
                    not isinstance(n, int) or isinstance(n, bool) or n < 1 for n in staffeln):
                raise ValueError(f"{ort}: staffeln muss eine Liste positiver Zahlen sein")
        bezeichnung = eintrag.get("label") or eintrag.get("tmdb") or eintrag.get("imdb") or eintrag.get("tvdb")
        if schluessel(eintrag) not in bekannt:
            warnungen.append(f"{ort} ({bezeichnung}): Titel gehört nicht zur Welt und wird nie angezeigt")
        if staffeln and tmdb and eintrag.get("tmdb"):
            tid = str(eintrag["tmdb"])
            if tid not in staffelzahl:
                try:
                    staffelzahl[tid] = int(tmdb.get("/tv/" + tid).get("number_of_seasons") or 0)
                except Exception:  # noqa: BLE001 – ohne Antwort nicht prüfbar
                    staffelzahl[tid] = 0
            if staffelzahl[tid] and max(staffeln) > staffelzahl[tid]:
                warnungen.append(f"{ort} ({bezeichnung}): Staffel {max(staffeln)} gibt es nicht (TMDB: {staffelzahl[tid]})")
    return warnungen


def erzeugen(regeln, alt_welten, tmdb=None, heute=None):
    """Erzeugt den Inhalt von welten.json. Gibt (dokument, bericht) zurück."""
    heute = heute or datetime.date.today().isoformat()
    # Bisherige Welten über Name, ID oder frühere IDs (aliase) finden – eine Umbenennung verliert keine Titel
    alt_nach_id = {}
    for w in alt_welten.get("welten", []):
        for k in [w.get("id"), welt_id(w.get("name"))] + list(w.get("aliase", [])):
            if k:
                alt_nach_id.setdefault(welt_id(k), w)
    welten, bericht = [], []
    for regel in regeln["welten"]:
        kandidaten = [regel.get("id"), welt_id(regel["name"])] + list(regel.get("aliase", []))
        alt_welt = next((alt_nach_id[welt_id(k)] for k in kandidaten if k and welt_id(k) in alt_nach_id), {})
        alt = alt_welt.get("titel", [])
        neu = tmdb_titel(tmdb, regel.get("tmdb", {}), heute) if tmdb else []
        titel, neu_hinzu = welt_zusammenfuehren(regel, alt, neu)
        entfernt = [e for e in alt if ist_ausgeschlossen(e, regel.get("ausschluss", []))]
        bericht.append((regel["name"], len(titel), neu_hinzu, entfernt))
        welt = {"name": regel["name"]}
        if regel.get("id"):
            welt["id"] = regel["id"]
        if regel.get("aliase"):
            welt["aliase"] = regel["aliase"]
        if regel.get("logo"):
            welt["logo"] = regel["logo"]
        if regel.get("trailer"):
            welt["trailer"] = regel["trailer"]
        if regel.get("chronologie"):
            # Reihenfolge nach Handlungszeit: geprüft, dann unverändert übernommen
            for warnung in chronologie_pruefen(regel["name"], regel["chronologie"], titel, tmdb):
                print("::warning::" + warnung)
            welt["chronologie"] = regel["chronologie"]
        welt.update({"studios": regel.get("studios", []), "sammlungen": regel.get("sammlungen", []),
                     "titel": titel, "ausschluss": regel.get("ausschluss", [])})
        welten.append(welt)
    dokument = {"beschreibung": BESCHREIBUNG, "quelle": QUELLE, "version": 2, "welten": welten}
    return dokument, bericht


def main():
    parser = argparse.ArgumentParser(description="Aktualisiert welten.json aus regeln.json und TMDB.")
    parser.add_argument("--ohne-tmdb", action="store_true", help="TMDB nicht abfragen, nur Regeln und Hand-Einträge übernehmen")
    parser.add_argument("--pruefen", action="store_true", help="nichts schreiben, nur Änderungen anzeigen")
    args = parser.parse_args()

    regeln = json.loads(REGELN.read_text(encoding="utf-8"))
    alt = json.loads(WELTEN.read_text(encoding="utf-8")) if WELTEN.exists() else {"welten": []}
    key = os.environ.get("TMDB_API_KEY", "").strip()
    tmdb = None
    if not args.ohne_tmdb:
        if not key:
            print("Kein TMDB_API_KEY gesetzt – es werden nur Regeln und Hand-Einträge übernommen.")
        else:
            tmdb = Tmdb(key)

    dokument, bericht = erzeugen(regeln, alt, tmdb)
    for name, anzahl, neu, entfernt in bericht:
        zeile = f"{name}: {anzahl} Titel"
        if neu:
            zeile += f", neu: {', '.join(e.get('name') or e['tmdb'] for e in neu[:10])}" + (" …" if len(neu) > 10 else "")
        if entfernt:
            zeile += f", entfernt (Ausschluss): {', '.join(e.get('name') or str(e.get('tmdb')) for e in entfernt)}"
        print(zeile)

    text = json.dumps(dokument, indent=1, ensure_ascii=False) + "\n"
    if args.pruefen:
        print("Geändert." if not WELTEN.exists() or WELTEN.read_text(encoding="utf-8") != text else "Keine Änderung.")
        return 0
    if WELTEN.exists() and WELTEN.read_text(encoding="utf-8") == text:
        print("welten.json ist bereits aktuell.")
        return 0
    WELTEN.write_text(text, encoding="utf-8")
    print("welten.json aktualisiert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
