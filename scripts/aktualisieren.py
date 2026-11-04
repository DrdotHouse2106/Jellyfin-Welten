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
import concurrent.futures
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
# Angekündigte Titel ohne echten Namen („Untitled X-Men Film“) – nie in die Listen
PLATZHALTER = re.compile(r"(?i)^\s*untitled\b")

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


def ist_platzhalter(eintrag):
    """Platzhalter-Titel („Untitled …“) gehören nie in eine Welt."""
    return bool(PLATZHALTER.search(eintrag.get("name") or ""))


def jahr_passt(datum, jahr):
    """TMDB-Datum (JJJJ-MM-TT) im gesuchten Jahr oder ein Jahr daneben (Festival- bzw. Länder-Termine)."""
    return bool(datum) and abs(int(datum[:4]) - int(jahr)) <= 1


def suche_titel(tmdb, eintrag):
    """Löst {"titel", "jahr", "typ"} über die TMDB-Suche auf: erster Treffer im passenden Jahr, sonst None."""
    serie = eintrag.get("typ") == "serie"
    params = {"query": eintrag["titel"]}
    if eintrag.get("jahr"):
        params["first_air_date_year" if serie else "primary_release_year"] = eintrag["jahr"]
    treffer = tmdb.get("/search/tv" if serie else "/search/movie", **params).get("results", [])
    if not treffer and eintrag.get("jahr"):
        # Ohne Jahresfilter erneut, dann Jahr ±1 prüfen
        treffer = tmdb.get("/search/tv" if serie else "/search/movie", query=eintrag["titel"]).get("results", [])
    for t in treffer:
        datum = (t.get("first_air_date") if serie else t.get("release_date")) or ""
        if not eintrag.get("jahr") or jahr_passt(datum, eintrag["jahr"]):
            return {"tmdb": str(t["id"]), "typ": "serie" if serie else "film",
                    "name": (t.get("name") if serie else t.get("title")) or t.get("original_title") or t.get("original_name"),
                    "datum": datum}
    return None


def suche_id(tmdb, art, name):
    """Sucht eine Sammlung bzw. Firma nach Namen: genauer Name zuerst, sonst der erste Treffer."""
    treffer = tmdb.get("/search/" + art, query=name, language="en-US").get("results", [])
    genau = [t for t in treffer if (t.get("name") or "").strip().lower() == name.strip().lower()]
    wahl = (genau or treffer or [None])[0]
    return (wahl["id"], wahl.get("name")) if wahl else (None, None)


def tmdb_titel(tmdb, quelle, heute, meldungen=None):
    """Sammelt die Titel einer Welt aus TMDB: [{tmdb, typ, name, datum}].

    Neben IDs („firmen“, „serien_firmen“, „sammlungen“, „personen“) gehen auch Namen, die über die TMDB-Suche
    aufgelöst werden: „firmen_suche“ ({"name", "min_stimmen"}), „sammlungen_suche“ (Namen, englisch wie bei TMDB)
    und „suche“ ({"titel", "jahr", "typ"}). Was dabei gefunden bzw. nicht gefunden wird, landet in „meldungen“.
    """
    meldungen = meldungen if meldungen is not None else []
    gefunden = []
    firmen = list(quelle.get("firmen", []))
    for firma in quelle.get("firmen_suche", []):
        fid, fname = suche_id(tmdb, "company", firma["name"])
        if fid is None:
            meldungen.append("Firma nicht gefunden: " + firma["name"])
            continue
        meldungen.append(f"Firma „{firma['name']}“ → {fname} ({fid})")
        firmen.append({**firma, "id": fid})
    sammlungen = list(quelle.get("sammlungen", []))
    for name in quelle.get("sammlungen_suche", []):
        sid, sname = suche_id(tmdb, "collection", name)
        if sid is None:
            meldungen.append("Sammlung nicht gefunden: " + name)
            continue
        meldungen.append(f"Sammlung „{name}“ → {sname} ({sid})")
        sammlungen.append(sid)
    for eintrag in quelle.get("suche", []):
        treffer = suche_titel(tmdb, eintrag)
        if treffer is None:
            meldungen.append(f"Titel nicht gefunden: {eintrag['titel']} ({eintrag.get('jahr', '?')})")
            continue
        meldungen.append(f"Titel „{eintrag['titel']}“ → {treffer['name']} ({treffer['datum'][:4]}, {treffer['tmdb']})")
        gefunden.append(treffer)
    for firma in firmen:
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
    for sammlung in sammlungen:
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
        if k is None or k in gesehen or ist_ausgeschlossen(eintrag, ausschluss) or ist_platzhalter(eintrag):
            return False
        if filtern and any(m.search(eintrag.get("name") or "") for m in muster):
            return False
        gesehen.add(k)
        ergebnis.append({f: eintrag[f] for f in ("tmdb", "imdb", "tvdb", "typ", "name") if eintrag.get(f)})
        # Angaben für die Abschnitte (einmal von TMDB geholt) bleiben erhalten
        ergebnis[-1].update({f: eintrag[f] for f in INFO_FELDER if f in eintrag})
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


INFO_FELDER = ("jahr", "genres", "reihe", "reihe_name", "firmen", "stimmen", "abschnitt")


def titel_info(tmdb, eintrag):
    """Holt Jahr, Genres, Filmreihe, Firmen und Stimmen eines Titels von TMDB (für die Abschnitte)."""
    serie = eintrag.get("typ") == "serie"
    daten = tmdb.get(("/tv/" if serie else "/movie/") + str(eintrag["tmdb"]))
    datum = (daten.get("first_air_date") if serie else daten.get("release_date")) or ""
    reihe = daten.get("belongs_to_collection") or {}
    return {"jahr": int(datum[:4]) if datum[:4].isdigit() else None,
            "genres": [g["id"] for g in daten.get("genres", []) if "id" in g],
            "reihe": reihe.get("id"), "reihe_name": reihe.get("name"),
            "firmen": [f["id"] for f in daten.get("production_companies", []) if "id" in f],
            "stimmen": daten.get("vote_count") or 0}


def anreichern(tmdb, titel, parallel=8):
    """Ergänzt fehlende Angaben (INFO_FELDER) für Titel mit TMDB-ID – nur einmal je Titel, danach stehen sie in welten.json."""
    offen = [t for t in titel if t.get("tmdb") and t.get("typ") in ("film", "serie") and "jahr" not in t]
    def hole(eintrag):
        try:
            return eintrag, titel_info(tmdb, eintrag)
        except Exception:  # noqa: BLE001 – ohne Antwort beim nächsten Lauf erneut
            return eintrag, None
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as pool:
        for eintrag, info in pool.map(hole, offen):
            if info is not None:
                eintrag.update(info)
    return len(offen)


def reihen_name(name):
    """Name einer Filmreihe ohne „Filmreihe“/„Collection“: „Halloween Filmreihe“ → „Halloween“."""
    if not name:
        return name
    return re.sub(r"\s*[-–]?\s*(Filmreihe|Collection|Reihe)\s*$", "", name, flags=re.I).strip() or name


def abschnitte_zuordnen(regeln_abschnitte, titel, tmdb=None, meldungen=None):
    """Ordnet jedem Titel genau einen Abschnitt zu (erste passende Regel gewinnt).

    Bedingungen einer Regel (alle müssen passen): "typ", "genres" (eines davon), "ohne_genres", "ab_jahr", "bis_jahr",
    "reihen" (TMDB-Sammlungs-IDs), "reihen_suche" (Namen), "firmen", "name_muster" (regulärer Ausdruck),
    "tmdb" (IDs), "titel_suche" ({"titel", "jahr", "typ"}). "je_reihe": true legt je Filmreihe einen eigenen
    Abschnitt an (Name der Reihe, ab "min_titel" Titeln, Standard 2). "zuerst": true prüft die Regel vor den anderen,
    ohne die Anzeigereihenfolge zu ändern. Gibt die Abschnitte in Anzeigereihenfolge zurück: [{"name", "min_stimmen_fehlend"?}].
    """
    meldungen = meldungen if meldungen is not None else []
    regeln = []
    for r in regeln_abschnitte:
        r = dict(r)
        ids = {str(x) for x in r.get("tmdb", [])}
        if tmdb:
            for e in r.get("titel_suche", []):
                treffer = suche_titel(tmdb, e)
                if treffer:
                    ids.add(treffer["tmdb"])
                else:
                    meldungen.append(f"Abschnitt „{r['name']}“: Titel nicht gefunden: {e['titel']} ({e.get('jahr', '?')})")
            reihen = set(r.get("reihen", []))
            for name in r.get("reihen_suche", []):
                rid, _ = suche_id(tmdb, "collection", name)
                if rid is None:
                    meldungen.append(f"Abschnitt „{r['name']}“: Sammlung nicht gefunden: {name}")
                else:
                    reihen.add(rid)
            r["reihen"] = sorted(reihen)
        r["_ids"] = ids
        regeln.append(r)

    def passt(r, t):
        if r.get("typ") and t.get("typ") != r["typ"]:
            return False
        g = set(t.get("genres") or [])
        if r.get("genres") and not g & set(r["genres"]):
            return False
        if r.get("ohne_genres") and g & set(r["ohne_genres"]):
            return False
        jahr = t.get("jahr")
        if r.get("ab_jahr") and (jahr is None or jahr < r["ab_jahr"]):
            return False
        if r.get("bis_jahr") and (jahr is None or jahr > r["bis_jahr"]):
            return False
        if r.get("reihen") and t.get("reihe") not in r["reihen"]:
            return False
        if r.get("je_reihe") and not t.get("reihe"):
            return False
        if r.get("firmen") and not set(t.get("firmen") or []) & set(r["firmen"]):
            return False
        if r.get("name_muster") and not re.search(r["name_muster"], t.get("name") or ""):
            return False
        if (r["_ids"] or r.get("titel_suche")) and str(t.get("tmdb")) not in r["_ids"]:
            return False
        return True

    # Prüfreihenfolge: Regeln mit "zuerst" vor den anderen (die Anzeigereihenfolge bleibt die der Liste)
    pruefen = [r for r in regeln if r.get("zuerst")] + [r for r in regeln if not r.get("zuerst")]
    # Eigener Abschnitt je Filmreihe erst ab "min_titel" Titeln (Standard 2), sonst greifen die folgenden Regeln
    reihen_zahl = {}
    for t in titel:
        if t.get("reihe"):
            reihen_zahl[t["reihe"]] = reihen_zahl.get(t["reihe"], 0) + 1
    je_reihe = {}
    for t in titel:
        t.pop("abschnitt", None)
        for r in pruefen:
            if r.get("je_reihe") and reihen_zahl.get(t.get("reihe"), 0) < r.get("min_titel", 2):
                continue
            if passt(r, t):
                if r.get("je_reihe"):
                    name = reihen_name(t.get("reihe_name")) or r["name"]
                    je_reihe.setdefault(r["name"], {}).setdefault(name, []).append(t.get("jahr") or 9999)
                    t["abschnitt"] = name
                else:
                    t["abschnitt"] = r["name"]
                break
    # Abschnitte je Filmreihe an der Stelle ihrer Regel, nach dem ersten Erscheinungsjahr
    ergebnis = []
    for r in regeln:
        namen = sorted(je_reihe.get(r["name"], {}).items(), key=lambda kv: (min(kv[1]), kv[0])) if r.get("je_reihe") else [(r["name"], None)]
        for name, _ in namen:
            if any(t.get("abschnitt") == name for t in titel) and name not in [a["name"] for a in ergebnis]:
                eintrag = {"name": name}
                if r.get("min_stimmen_fehlend"):
                    eintrag["min_stimmen_fehlend"] = r["min_stimmen_fehlend"]
                ergebnis.append(eintrag)
    return ergebnis


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
        meldungen = []
        neu = tmdb_titel(tmdb, regel.get("tmdb", {}), heute, meldungen) if tmdb else []
        for meldung in meldungen:
            print(("::warning::" if "nicht gefunden" in meldung else "") + regel["name"] + ": " + meldung)
        titel, neu_hinzu = welt_zusammenfuehren(regel, alt, neu)
        if tmdb and regel.get("abschnitte"):
            angereichert = anreichern(tmdb, titel)
            if angereichert:
                print(f"{regel['name']}: {angereichert} Titel mit Genres, Filmreihe und Jahr ergänzt")
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
        if regel.get("abschnitte") and not tmdb:
            # Ohne TMDB lassen sich Suchen nicht auflösen: bisherige Zuordnung behalten
            welt["abschnitte"] = alt_welt.get("abschnitte", [])
        elif regel.get("abschnitte"):
            abschnitt_meldungen = []
            welt["abschnitte"] = abschnitte_zuordnen(regel["abschnitte"], titel, tmdb, abschnitt_meldungen)
            for meldung in abschnitt_meldungen:
                print("::warning::" + regel["name"] + ": " + meldung)
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
