#!/usr/bin/env python3
# Eigene Figuren-Icons fuer Jellyfin-Welten (flach, OpenMoji-aehnlicher Stil, viewBox 72x72)
# Urheber: DrdotHouse2106 – Lizenz CC BY-SA 4.0. Die Figuren erinnern nur an bekannte Welten,
# es sind keine offiziellen Figuren. Schreibt die SVGs nach svg/<kategorie>/<id>.svg.
import os, json

S = 'stroke="#000" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"'
HAUT = "#f3c79a"

def sw(w):
    return S.replace('stroke-width="2"', f'stroke-width="{w}"')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "svg")

def augen(y=34, dx=7, r=2):
    return f'<circle cx="{36-dx}" cy="{y}" r="{r}"/><circle cx="{36+dx}" cy="{y}" r="{r}"/>'

def laecheln(y=44):
    return f'<path d="M30 {y} Q36 {y+5} 42 {y}" fill="none" {S}/>'

ICONS = {}

ICONS["superhelden/netz-held"] = ("Netz-Held", f'''
<defs><clipPath id="k"><ellipse cx="36" cy="34" rx="18" ry="22"/></clipPath></defs>
<path d="M10 72 Q12 56 36 56 Q60 56 62 72Z" fill="#1d4ed8" {S}/>
<path d="M27 56 L36 66 L45 56Z" fill="#dc2626" {S}/>
<ellipse cx="36" cy="34" rx="18" ry="22" fill="#dc2626"/>
<g clip-path="url(#k)" fill="none" stroke="#000" stroke-width="1">
<path d="M36 34 L36 8 M36 34 L14 18 M36 34 L58 18 M36 34 L12 38 M36 34 L60 38 M36 34 L20 58 M36 34 L52 58 M36 34 L36 60"/>
<path d="M28 30 Q36 26 44 30 Q48 36 44 42 Q36 46 28 42 Q24 36 28 30Z"/>
<path d="M22 22 Q36 14 50 22 Q58 36 50 50 Q36 58 22 50 Q14 36 22 22Z"/></g>
<ellipse cx="36" cy="34" rx="18" ry="22" fill="none" {S}/>
<path d="M21 30 Q27 23 33 31 Q28 38 21 30Z" fill="#fff" {S}/>
<path d="M51 30 Q45 23 39 31 Q44 38 51 30Z" fill="#fff" {S}/>''')

ICONS["superhelden/fledermaus-held"] = ("Fledermaus-Held", f'''
<path d="M6 72 Q10 52 36 52 Q62 52 66 72Z" fill="#374151" {S}/>
<path d="M22 40 Q22 58 36 58 Q50 58 50 40Z" fill="{HAUT}" {S}/>
<path d="M30 50 Q36 52 42 50" fill="none" {S}/>
<path d="M18 44 L18 24 L21 8 L28 18 L44 18 L51 8 L54 24 L54 44 Q50 40 46 42 L26 42 Q22 40 18 44Z" fill="#1f2937" {S}/>
<path d="M24 31 L32 33 L31 35 L25 34Z" fill="#fff" {S}/>
<path d="M48 31 L40 33 L41 35 L47 34Z" fill="#fff" {S}/>''')

ICONS["superhelden/sternen-schild"] = ("Sternenschild", f'''
<path d="M14 12 Q36 6 58 12 L58 34 Q58 56 36 66 Q14 56 14 34Z" fill="#1d4ed8" {S}/>
<path d="M20 17 Q36 12 52 17 L52 34 Q52 51 36 59 Q20 51 20 34Z" fill="#e5e7eb" {S}/>
<path d="M36 22 L39.5 31 L49 31 L41.5 37 L44.5 46 L36 40.5 L27.5 46 L30.5 37 L23 31 L32.5 31Z" fill="#dc2626" {S}/>''')

ICONS["superhelden/kriegerin"] = ("Kriegerin", f'''
<path d="M14 70 Q12 40 20 22 Q36 8 52 22 Q60 40 58 70Z" fill="#111827" {S}/>
<path d="M12 72 Q14 58 36 58 Q58 58 60 72Z" fill="#b91c1c" {S}/>
<path d="M24 64 L36 58 L48 64" fill="none" stroke="#facc15" stroke-width="3"/>
<ellipse cx="36" cy="38" rx="15" ry="18" fill="{HAUT}" {S}/>
<path d="M21 30 Q36 18 51 30 L51 26 Q36 14 21 26Z" fill="#facc15" {S}/>
<path d="M36 19 L39 24 L36 29 L33 24Z" fill="#dc2626" {S}/>
{augen(38, 6)}{laecheln(46)}''')

ICONS["superhelden/gruener-riese"] = ("Grüner Riese", f'''
<path d="M4 72 Q8 50 36 50 Q64 50 68 72Z" fill="#7c3aed" {S}/>
<path d="M16 34 Q14 56 36 60 Q58 56 56 34 Q56 14 36 14 Q16 14 16 34Z" fill="#4d9e3a" {S}/>
<path d="M16 30 L18 14 L24 18 L28 10 L34 15 L40 9 L45 15 L52 11 L54 20 L57 30 Q50 22 36 22 Q22 22 16 30Z" fill="#111827" {S}/>
<path d="M23 32 L32 35 M49 32 L40 35" fill="none" {sw(3)}/>
{augen(38, 7, 2.2)}
<path d="M27 48 L45 48 L43 53 L29 53Z" fill="#fff" {S}/>
<path d="M33 48 L33 53 M39 48 L39 53" {sw(1)}/>''')

ICONS["superhelden/blitz-held"] = ("Blitz-Held", f'''
<path d="M10 72 Q12 56 36 56 Q60 56 62 72Z" fill="#dc2626" {S}/>
<circle cx="36" cy="64" r="5" fill="#fde047" {S}/>
<path d="M18 36 Q18 12 36 12 Q54 12 54 36 L54 44 L18 44Z" fill="#dc2626" {S}/>
<path d="M22 40 Q22 58 36 58 Q50 58 50 40Z" fill="{HAUT}" {S}/>
<path d="M17 28 L8 24 L15 34Z M55 28 L64 24 L57 34Z" fill="#fde047" {S}/>
<path d="M38 14 L31 26 L36 26 L33 35 L41 22 L36 22Z" fill="#fde047" {S}/>
<path d="M24 34 L32 35 L31 38 L25 37Z" fill="#fff" {S}/>
<path d="M48 34 L40 35 L41 38 L47 37Z" fill="#fff" {S}/>
{laecheln(49)}''')

ICONS["superhelden/donner-held"] = ("Donner-Held", f'''
<path d="M8 72 Q10 54 36 54 Q62 54 64 72Z" fill="#b91c1c" {S}/>
<path d="M22 56 Q36 62 50 56 L50 72 L22 72Z" fill="#6b7280" {S}/>
<path d="M18 40 Q16 62 36 64 Q56 62 54 40" fill="#eab308" {S}/>
<ellipse cx="36" cy="38" rx="14" ry="16" fill="{HAUT}" {S}/>
<path d="M24 46 Q36 58 48 46 Q46 54 36 56 Q26 54 24 46Z" fill="#eab308" {S}/>
<path d="M20 30 Q20 14 36 14 Q52 14 52 30Z" fill="#9ca3af" {S}/>
<path d="M20 26 L6 14 L10 26 L4 24 L12 32 L20 31Z M52 26 L66 14 L62 26 L68 24 L60 32 L52 31Z" fill="#e5e7eb" {S}/>
{augen(38, 6)}''')

ICONS["superhelden/eisen-held"] = ("Eisen-Held", f'''
<path d="M10 72 Q12 56 36 56 Q60 56 62 72Z" fill="#b91c1c" {S}/>
<circle cx="36" cy="64" r="5" fill="#bae6fd" {S}/>
<path d="M18 30 Q18 10 36 10 Q54 10 54 30 L54 44 Q52 56 36 58 Q20 56 18 44Z" fill="#b91c1c" {S}/>
<path d="M23 26 Q36 20 49 26 L49 44 Q46 52 36 53 Q26 52 23 44Z" fill="#fbbf24" {S}/>
<path d="M26 32 L33 33 L33 35 L26 34Z M46 32 L39 33 L39 35 L46 34Z" fill="#e0f2fe" {S}/>
<path d="M30 46 L42 46" {S}/>''')

ICONS["maerchen/eis-prinzessin"] = ("Eisprinzessin", f'''
<path d="M12 72 Q14 56 36 56 Q58 56 60 72Z" fill="#7dd3fc" {S}/>
<path d="M18 40 Q16 16 36 14 Q56 16 54 40 Q52 30 36 28 Q20 30 18 40Z" fill="#fde68a" {S}/>
<ellipse cx="36" cy="40" rx="14" ry="16" fill="{HAUT}" {S}/>
<path d="M22 36 Q24 24 36 24 Q48 24 50 36 Q46 28 36 28 Q26 28 22 36Z" fill="#fde68a" {S}/>
<path d="M50 34 Q58 46 52 58 Q48 66 54 70" fill="none" stroke="#000" stroke-width="7" stroke-linecap="round"/>
<path d="M50 34 Q58 46 52 58 Q48 66 54 70" fill="none" stroke="#fde68a" stroke-width="4.5" stroke-linecap="round"/>
<path d="M28 22 L30 16 L33 21 L36 14 L39 21 L42 16 L44 22Z" fill="#e0f2fe" {S}/>
{augen(40, 6)}{laecheln(48)}''')

ICONS["maerchen/meerjungfrau"] = ("Meerjungfrau", f'''
<path d="M12 72 Q14 58 36 58 Q58 58 60 72Z" fill="{HAUT}" {S}/>
<path d="M26 62 Q30 58 34 62 Q30 66 26 62Z M38 62 Q42 58 46 62 Q42 66 38 62Z" fill="#a855f7" {S}/>
<path d="M14 66 Q8 36 20 20 Q36 8 52 20 Q64 36 58 66 Q54 48 52 36 L20 36 Q18 48 14 66Z" fill="#dc2626" {S}/>
<ellipse cx="36" cy="38" rx="14" ry="16" fill="{HAUT}" {S}/>
<path d="M22 34 Q26 20 40 22 Q50 24 50 34 Q42 26 30 30Z" fill="#dc2626" {S}/>
{augen(40, 6)}{laecheln(47)}''')

ICONS["maerchen/zauberer"] = ("Zauberer", f'''
<path d="M10 72 Q12 56 36 56 Q60 56 62 72Z" fill="#1e3a8a" {S}/>
<path d="M20 44 Q20 70 36 70 Q52 70 52 44Z" fill="#f3f4f6" {S}/>
<ellipse cx="36" cy="38" rx="13" ry="13" fill="{HAUT}" {S}/>
<path d="M22 42 Q24 68 36 70 Q48 68 50 42 Q44 48 36 48 Q28 48 22 42Z" fill="#f3f4f6" {S}/>
<path d="M30 46 Q36 49 42 46" fill="none" {S}/>
<path d="M12 30 Q36 22 60 30 Q56 34 36 32 Q16 34 12 30Z" fill="#1d4ed8" {S}/>
<path d="M20 30 L40 2 L52 30Z" fill="#1d4ed8" {S}/>
<path d="M36 14 L37.5 18 L41.5 18 L38.5 20.5 L39.5 24.5 L36 22 L32.5 24.5 L33.5 20.5 L30.5 18 L34.5 18Z" fill="#fde047"/>
<circle cx="44" cy="24" r="1.5" fill="#fde047"/><circle cx="28" cy="26" r="1.2" fill="#fde047"/>
{augen(38, 5, 1.8)}''')

ICONS["maerchen/fee"] = ("Fee", f'''
<path d="M30 52 Q10 36 8 50 Q8 62 30 58Z M42 52 Q62 36 64 50 Q64 62 42 58Z" fill="#a7f3d0" fill-opacity="0.9" {S}/>
<path d="M30 52 Q16 60 14 68 Q24 70 32 60Z M42 52 Q56 60 58 68 Q48 70 40 60Z" fill="#a7f3d0" fill-opacity="0.9" {S}/>
<path d="M26 72 L30 52 L42 52 L46 72Z" fill="#22c55e" {S}/>
<circle cx="36" cy="18" r="7" fill="#fcd34d" {S}/>
<ellipse cx="36" cy="36" rx="12" ry="13" fill="{HAUT}" {S}/>
<path d="M24 34 Q26 22 36 22 Q46 22 48 34 Q42 28 36 28 Q30 28 24 34Z" fill="#fcd34d" {S}/>
{augen(37, 5, 1.8)}{laecheln(42)}
<path d="M58 14 L59.5 18 L63.5 18 L60.5 20.5 L61.5 24.5 L58 22 L54.5 24.5 L55.5 20.5 L52.5 18 L56.5 18Z" fill="#fde047" {sw(1)}/>''')

ICONS["maerchen/loewen-koenig"] = ("Löwenkönig", f'''
<path d="M36 6 Q48 8 52 14 Q62 16 62 28 Q68 38 60 46 Q62 58 50 60 Q44 68 36 66 Q28 68 22 60 Q10 58 12 46 Q4 38 10 28 Q10 16 20 14 Q24 8 36 6Z" fill="#b45309" {S}/>
<ellipse cx="36" cy="38" rx="16" ry="17" fill="#f59e0b" {S}/>
<circle cx="24" cy="24" r="4" fill="#f59e0b" {S}/><circle cx="48" cy="24" r="4" fill="#f59e0b" {S}/>
<ellipse cx="36" cy="46" rx="8" ry="6" fill="#fde68a" {S}/>
<path d="M33 42 L39 42 L36 45Z" fill="#78350f" {S}/>
<path d="M36 45 L36 48 M32 50 Q36 52 40 50" fill="none" {S}/>
{augen(36, 6, 2)}
<path d="M27 16 L29 8 L33 13 L36 6 L39 13 L43 8 L45 16Z" fill="#facc15" {S}/>''')

ICONS["maerchen/schneemann"] = ("Schneemann", f'''
<circle cx="36" cy="58" r="16" fill="#f8fafc" {S}/>
<circle cx="36" cy="30" r="17" fill="#f8fafc" {S}/>
<circle cx="36" cy="52" r="1.8"/><circle cx="36" cy="60" r="1.8"/>
<path d="M36 13 L34 4 M36 13 L40 5 M34 7 L30 4 M39 8 L43 6" fill="none" stroke="#78350f" stroke-width="2" stroke-linecap="round"/>
<path d="M36 31 L50 34 L36 35Z" fill="#f97316" {S}/>
{augen(25, 6, 2.2)}
<path d="M29 40 Q36 44 43 40" fill="none" {S}/>''')

ICONS["weltraum/lichtschwert-ritter"] = ("Lichtschwert-Ritter", f'''
<path d="M8 72 Q8 50 22 40 L50 40 Q64 50 64 72Z" fill="#78350f" {S}/>
<path d="M16 46 Q14 14 36 12 Q58 14 56 46 Q46 52 36 52 Q26 52 16 46Z" fill="#92400e" {S}/>
<ellipse cx="36" cy="36" rx="12" ry="14" fill="{HAUT}" {S}/>
{augen(35, 5, 1.8)}
<path d="M31 43 L41 43" {S}/>
<path d="M58 54 L68 8" stroke="#000" stroke-width="7" stroke-linecap="round"/>
<path d="M58 54 L68 8" stroke="#7dd3fc" stroke-width="4" stroke-linecap="round"/>
<path d="M58 54 L68 8" stroke="#fff" stroke-width="1.2" stroke-linecap="round"/>
<rect x="52" y="54" width="10" height="5" rx="1" fill="#9ca3af" {S} transform="rotate(-77.7 57 56.5)"/>
<circle cx="55" cy="62" r="4" fill="{HAUT}" {S}/>''')

ICONS["weltraum/droide"] = ("Droide", f'''
<path d="M18 30 L54 30 L54 62 Q54 66 50 66 L22 66 Q18 66 18 62Z" fill="#f3f4f6" {S}/>
<path d="M12 34 L18 34 L18 64 L12 68Z M60 34 L54 34 L54 64 L60 68Z" fill="#d1d5db" {S}/>
<path d="M18 30 Q18 8 36 8 Q54 8 54 30Z" fill="#cbd5e1" {S}/>
<path d="M22 22 L50 22 L50 26 L22 26Z" fill="#1d4ed8" {S}/>
<circle cx="36" cy="16" r="4" fill="#111827" {S}/><circle cx="37" cy="15" r="1.2" fill="#fff"/>
<rect x="24" y="36" width="10" height="8" fill="#1d4ed8" {S}/>
<rect x="38" y="36" width="10" height="4" fill="#1d4ed8" {S}/>
<path d="M26 50 L46 50 M26 56 L46 56" {S}/>''')

ICONS["weltraum/kopfgeldjaeger"] = ("Kopfgeldjäger", f'''
<path d="M8 72 Q10 54 36 54 Q62 54 64 72Z" fill="#57534e" {S}/>
<path d="M18 30 Q18 8 36 8 Q54 8 54 30 L54 50 Q50 56 36 56 Q22 56 18 50Z" fill="#a8a29e" {S}/>
<path d="M24 26 L48 26 L48 32 L40 32 L40 50 L32 50 L32 32 L24 32Z" fill="#111827" {S}/>
<path d="M22 50 L28 44 M50 50 L44 44" {S}/>
<path d="M18 22 Q36 14 54 22" fill="none" {sw(1.5)}/>''')

ICONS["weltraum/gruener-weiser"] = ("Grüner Weiser", f'''
<path d="M10 72 Q12 54 36 54 Q60 54 62 72Z" fill="#a16207" {S}/>
<path d="M30 54 L36 64 L42 54" fill="none" {S}/>
<path d="M22 32 L2 22 L8 36 L22 42Z M50 32 L70 22 L64 36 L50 42Z" fill="#84cc16" {S}/>
<path d="M8 28 L20 34 M64 28 L52 34" {sw(1)}/>
<ellipse cx="36" cy="38" rx="15" ry="16" fill="#84cc16" {S}/>
<path d="M25 26 Q30 22 34 26 M38 26 Q42 22 47 26" fill="none" stroke="#e5e7eb" stroke-width="2" stroke-linecap="round"/>
<path d="M26 32 Q31 30 34 33 M38 33 Q41 30 46 32" fill="none" {sw(1.2)}/>
{augen(37, 6, 2.4)}
<path d="M30 47 Q36 50 42 47" fill="none" {S}/>''')

ICONS["weltraum/astronautin"] = ("Astronautin", f'''
<path d="M10 72 Q12 56 36 56 Q60 56 62 72Z" fill="#f8fafc" {S}/>
<rect x="30" y="60" width="12" height="7" rx="1" fill="#93c5fd" {S}/>
<circle cx="36" cy="34" r="24" fill="#f8fafc" {S}/>
<ellipse cx="36" cy="35" rx="16" ry="15" fill="#fb923c" {S}/>
<path d="M26 28 Q30 23 36 23" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity="0.8"/>
<circle cx="14" cy="34" r="3" fill="#cbd5e1" {S}/><circle cx="58" cy="34" r="3" fill="#cbd5e1" {S}/>''')

KATEGORIEN = [
    ("superhelden", "Superhelden"),
    ("maerchen", "Märchen & Magie"),
    ("weltraum", "Weltraum-Abenteuer"),
]

os.makedirs(OUT, exist_ok=True)
for key, (name, body) in ICONS.items():
    os.makedirs(os.path.join(OUT, key.split("/")[0]), exist_ok=True)
    with open(os.path.join(OUT, key + ".svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72" width="512" height="512">{body}</svg>\n')

liste = [{"id": k.split("/")[1], "kategorie": k.split("/")[0], "name": n} for k, (n, _) in ICONS.items()]
json.dump({"kategorien": KATEGORIEN, "icons": liste}, open(os.path.join(OUT, "liste.json"), "w"), ensure_ascii=False, indent=1)
print(len(ICONS), "Icons geschrieben")
