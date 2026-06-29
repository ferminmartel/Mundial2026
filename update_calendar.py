"""
update_calendar.py
==================
Fetchea resultados del Mundial 2026 desde la ESPN API,
actualiza bracket.json con los equipos clasificados y
regenera mundial2026.ics.
"""

import json, os, sys, subprocess
from datetime import datetime, timedelta
import urllib.request, urllib.error

ESPN_STANDINGS = "https://site.api.espn.com/apis/v2/sports/soccer/FIFA.WORLD/standings?season=2026"
ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/soccer/FIFA.WORLD/scoreboard"

COMPLETED_STATUSES = {
    "STATUS_FINAL", "STATUS_FULL_TIME",
    "STATUS_FULL_PEN", "STATUS_FULL_ET",
}

# Estructura del bracket (fixture fijo de FIFA 2026)
BRACKET_STRUCTURE = {
    73: ("2nd_A", "2nd_B"),
    74: ("1st_E", "best3rd_ABCDF"),
    75: ("1st_F", "2nd_C"),
    76: ("1st_C", "2nd_F"),
    77: ("1st_I", "best3rd_CDFGH"),
    78: ("2nd_E", "2nd_I"),
    79: ("1st_A", "best3rd_CEFHI"),
    80: ("1st_L", "best3rd_EHIJK"),
    81: ("1st_D", "best3rd_BEFIJ"),
    82: ("1st_G", "best3rd_AEHIJ"),
    83: ("2nd_K", "2nd_L"),
    84: ("1st_H", "2nd_J"),
    85: ("1st_B", "best3rd_EFGIJ"),
    86: ("1st_J", "2nd_H"),
    87: ("1st_K", "best3rd_DEIJL"),
    88: ("2nd_D", "2nd_G"),
}

FEEDS = {
    89: (74, 77), 90: (73, 75), 91: (76, 78),  92: (79, 80),
    93: (83, 84), 94: (81, 82), 95: (86, 88),  96: (85, 87),
    97: (89, 90), 98: (93, 94), 99: (91, 92), 100: (95, 96),
    101: (97, 98), 102: (99, 100),
    104: (101, 102),
}


# ──────────────────────────────────────────────────────
def fetch_json(url):
    print(f"  → GET {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode()
            data = json.loads(raw)
            print(f"     OK ({len(raw)} bytes)")
            return data
    except Exception as e:
        print(f"     ERROR: {e}")
        return None


def get_standings():
    """
    Devuelve: {
      "positions": {"1st_A":"MEX", "2nd_A":"RSA", ...},
      "thirds":    [("RSA","A",pts,gd,gf), ...]  ordenado mejor→peor
    }
    """
    data = fetch_json(ESPN_STANDINGS)
    if not data:
        return None

    positions = {}
    thirds = []

    children = data.get("children", [])
    print(f"  Grupos encontrados: {len(children)}")

    for group in children:
        raw_name = group.get("name", "")
        letter = raw_name.replace("Group ", "").strip()
        if not letter or len(letter) != 1:
            print(f"  ⚠ Grupo ignorado: '{raw_name}'")
            continue

        entries = group.get("standings", {}).get("entries", [])
        teams = []
        for e in entries:
            code = e["team"].get("abbreviation") or e["team"].get("shortDisplayName", "???")
            stats = {s["name"]: s["value"] for s in e.get("stats", [])}
            pts = int(stats.get("points", 0))
            gd  = int(stats.get("pointDifferential", 0))
            gf  = int(stats.get("pointsFor", stats.get("goalsFor", 0)))
            gp  = int(stats.get("gamesPlayed", 0))
            teams.append((code, pts, gd, gf, gp))

        # Ordenar por puntos → DG → GF
        teams.sort(key=lambda x: (-x[1], -x[2], -x[3]))

        if len(teams) >= 1:
            positions[f"1st_{letter}"] = teams[0][0]
        if len(teams) >= 2:
            positions[f"2nd_{letter}"] = teams[1][0]
        if len(teams) >= 3:
            thirds.append((teams[2][0], letter, teams[2][1], teams[2][2], teams[2][3]))

        print(f"  Grupo {letter}: {[t[0] for t in teams]}")

    # Ordenar terceros: pts → gd → gf
    thirds.sort(key=lambda x: (-x[2], -x[3], -x[4]))
    return {"positions": positions, "thirds": thirds}


def get_best3rd(groups_str, thirds):
    """Mejor tercer puesto de los grupos indicados."""
    allowed = set(groups_str)
    for t in thirds:
        if t[1] in allowed:
            return t[0]
    return None


def resolve_bracket(positions, thirds):
    bracket = {}
    for match_num, (slot1, slot2) in BRACKET_STRUCTURE.items():
        t1 = positions.get(slot1)
        if t1 is None and "best3rd_" in slot1:
            t1 = get_best3rd(slot1.replace("best3rd_", ""), thirds)
        t2 = positions.get(slot2)
        if t2 is None and "best3rd_" in slot2:
            t2 = get_best3rd(slot2.replace("best3rd_", ""), thirds)
        if t1: bracket[f"p{match_num}_t1"] = t1
        if t2: bracket[f"p{match_num}_t2"] = t2
    return bracket


def fetch_scoreboard_day(date_str):
    """Fetches scoreboard for a single YYYYMMDD date."""
    return fetch_json(f"{ESPN_SCOREBOARD}?dates={date_str}")


def get_completed_results(date_strs):
    """
    Returns {frozenset(code1,code2): (score_str, winner)} for completed matches.
    date_strs: list of "YYYYMMDD" strings
    """
    results = {}
    for ds in date_strs:
        data = fetch_scoreboard_day(ds)
        if not data:
            continue
        for event in data.get("events", []):
            try:
                comp = event["competitions"][0]
                status = comp["status"]["type"]["name"]
                if status not in COMPLETED_STATUSES:
                    continue
                c = comp["competitors"]
                h_code  = c[0]["team"].get("abbreviation", "???")
                a_code  = c[1]["team"].get("abbreviation", "???")
                h_score = int(float(c[0].get("score") or 0))
                a_score = int(float(c[1].get("score") or 0))

                # Determinar ganador
                if h_score > a_score:
                    winner = h_code
                elif a_score > h_score:
                    winner = a_code
                else:
                    winner = next(
                        (x["team"].get("abbreviation") for x in c if x.get("winner")),
                        h_code
                    )

                score_str = f"{h_score}-{a_score}"
                if status == "STATUS_FULL_PEN":
                    score_str += " (pen)"

                key = frozenset([h_code, a_code])
                results[key] = (score_str, winner)
                print(f"  {h_code} {score_str} {a_code}  [{status}]")
            except Exception as ex:
                print(f"  ⚠ Error parsing event: {ex}")
    return results


def dates_range(start_str, end_str):
    """Generate list of YYYYMMDD strings between start and end (inclusive)."""
    start = datetime.strptime(start_str, "%Y%m%d")
    end   = datetime.strptime(end_str,   "%Y%m%d")
    out   = []
    cur   = start
    while cur <= end:
        out.append(cur.strftime("%Y%m%d"))
        cur += timedelta(days=1)
    return out


def advance_knockout(bracket, results):
    """Fill rounds 89→104 based on winners of previous rounds."""
    # Build winner_of map from results
    winner_of = {}   # match_num → winner_code
    loser_of  = {}

    for match_num in range(73, 105):
        t1 = bracket.get(f"p{match_num}_t1")
        t2 = bracket.get(f"p{match_num}_t2")
        if not t1 or not t2:
            continue
        key = frozenset([t1, t2])
        if key in results:
            score_str, winner = results[key]
            loser = t2 if winner == t1 else t1
            winner_of[match_num] = winner
            loser_of[match_num]  = loser
            # Store score in bracket
            c1, c2 = sorted([t1, t2])
            bracket[f"result_{c1}_{c2}"] = score_str

    # Advance winners
    for match_num, (f1, f2) in FEEDS.items():
        if f1 in winner_of:
            bracket[f"p{match_num}_t1"] = winner_of[f1]
        if f2 in winner_of:
            bracket[f"p{match_num}_t2"] = winner_of[f2]

    # 3rd place: losers of semis
    if 101 in loser_of: bracket["p103_t1"] = loser_of[101]
    if 102 in loser_of: bracket["p103_t2"] = loser_of[102]

    return bracket


def main():
    print(f"\n{'='*55}")
    print(f"🔄  Actualizando calendario Mundial 2026")
    print(f"    {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}\n")

    # ── Cargar bracket existente ──
    existing = {}
    if os.path.exists("bracket.json"):
        with open("bracket.json") as f:
            existing = json.load(f)
        print(f"bracket.json existente: {len(existing)} entradas\n")

    # ── 1. Standings → posiciones de grupo ──
    print("── 1. Standings de grupos ──")
    sdata = get_standings()

    if sdata and sdata["positions"]:
        print(f"\n  → {len(sdata['positions'])} posiciones obtenidas")
        bracket = resolve_bracket(sdata["positions"], sdata["thirds"])
        print(f"  → {len(bracket)} slots del bracket resueltos")
        # Preservar entradas viejas que no se pisaron
        for k, v in existing.items():
            if k not in bracket:
                bracket[k] = v
    else:
        print("  ⚠ Sin datos de standings — usando bracket existente")
        bracket = existing.copy()

    # ── 2. Resultados de partidos (hoy y días anteriores) ──
    today     = datetime.utcnow()
    yesterday = today - timedelta(days=1)
    # Rango de la fase eliminatoria completa
    ko_dates  = dates_range("20260628", today.strftime("%Y%m%d"))
    # Solo buscar en días que ya pasaron o son hoy
    ko_dates  = [d for d in ko_dates if d <= today.strftime("%Y%m%d")]

    if ko_dates:
        print(f"\n── 2. Resultados eliminatorios ({ko_dates[0]} → {ko_dates[-1]}) ──")
        results = get_completed_results(ko_dates)
        print(f"  → {len(results)} partidos terminados")
        bracket = advance_knockout(bracket, results)

        # También guardar resultados de fase de grupos si están en el scoreboard de hoy
        # (ESPN a veces incluye resultados recientes en el scoreboard del día)
        today_str = today.strftime("%Y%m%d")
        group_data = fetch_scoreboard_day(today_str)
        if group_data:
            for event in group_data.get("events", []):
                try:
                    comp  = event["competitions"][0]
                    if comp["status"]["type"]["name"] not in COMPLETED_STATUSES:
                        continue
                    c      = comp["competitors"]
                    h_code = c[0]["team"].get("abbreviation", "???")
                    a_code = c[1]["team"].get("abbreviation", "???")
                    h_s    = int(float(c[0].get("score") or 0))
                    a_s    = int(float(c[1].get("score") or 0))
                    c1, c2 = sorted([h_code, a_code])
                    key    = f"result_{c1}_{c2}"
                    if key not in bracket:
                        bracket[key] = f"{h_s}-{a_s}"
                except Exception:
                    pass

    # ── 3. Guardar bracket.json ──
    with open("bracket.json", "w") as f:
        json.dump(bracket, f, indent=2, ensure_ascii=False)
    print(f"\n✅  bracket.json guardado — {len(bracket)} entradas")

    # ── 4. Regenerar ICS ──
    print("\n── 4. Regenerando mundial2026.ics ──")
    r = subprocess.run([sys.executable, "build_ics.py"], capture_output=True, text=True)
    if r.returncode == 0:
        print(r.stdout.strip() or "  OK")
    else:
        print(f"❌  Error en build_ics.py:\n{r.stderr}")
        sys.exit(1)

    print("\n✅  ¡Listo!\n")


if __name__ == "__main__":
    main()
