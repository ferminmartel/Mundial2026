"""
update_calendar.py  -  Mundial 2026
Calcula standings desde resultados ya almacenados,
resuelve el bracket eliminatorio y regenera el ICS.
"""

import json, os, sys, subprocess
from datetime import datetime, timedelta
from itertools import combinations
import urllib.request

# --- Equipos por grupo (fixture fijo FIFA 2026) ---
GROUP_TEAMS = {
    "A": ["MEX","RSA","KOR","CZE"],
    "B": ["CAN","BIH","SUI","QAT"],
    "C": ["BRA","MAR","SCO","HAI"],
    "D": ["USA","PAR","TUR","AUS"],
    "E": ["GER","CUW","CIV","ECU"],
    "F": ["NED","JPN","SWE","TUN"],
    "G": ["BEL","EGY","IRN","NZL"],
    "H": ["ESP","CPV","KSA","URU"],
    "I": ["FRA","SEN","IRQ","NOR"],
    "J": ["ARG","ALG","AUT","JOR"],
    "K": ["POR","COD","UZB","COL"],
    "L": ["ENG","CRO","GHA","PAN"],
}

# --- Bracket fixture fijo FIFA 2026 ---
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
    89:  (74, 77), 90:  (73, 75), 91:  (76, 78),  92:  (79, 80),
    93:  (83, 84), 94:  (81, 82), 95:  (86, 88),  96:  (85, 87),
    97:  (89, 90), 98:  (93, 94), 99:  (91, 92),  100: (95, 96),
    101: (97, 98), 102: (99, 100),
    104: (101, 102),
}

ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/FIFA.WORLD/scoreboard"
DONE = {"STATUS_FINAL", "STATUS_FULL_TIME", "STATUS_FULL_PEN", "STATUS_FULL_ET"}


def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("    WARNING fetch %s: %s" % (url, e))
        return None


def rkey(t1, t2):
    c1, c2 = sorted([t1, t2])
    return "result_%s_%s" % (c1, c2)


def parse_score(s):
    try:
        parts = s.split(" ")[0].split("-")
        return int(parts[0]), int(parts[1])
    except Exception:
        return None, None


def fetch_results(date_list):
    """Fetch completed match results for given dates. Returns {rkey: score_str}."""
    found = {}
    for ds in date_list:
        data = fetch_json("%s?dates=%s" % (ESPN, ds))
        if not data:
            continue
        for ev in data.get("events", []):
            try:
                comp = ev["competitions"][0]
                status = comp["status"]["type"]["name"]
                if status not in DONE:
                    continue
                c = comp["competitors"]
                h = c[0]["team"].get("abbreviation", "???")
                a = c[1]["team"].get("abbreviation", "???")
                hs = int(float(c[0].get("score") or 0))
                as_ = int(float(c[1].get("score") or 0))
                suffix = " (pen)" if status == "STATUS_FULL_PEN" else ""
                c1, c2 = sorted([h, a])
                s1 = hs if h == c1 else as_
                s2 = as_ if h == c1 else hs
                key = "result_%s_%s" % (c1, c2)
                found[key] = "%d-%d%s" % (s1, s2, suffix)
                print("    %s %d-%d %s" % (h, hs, as_, a))
            except Exception as ex:
                print("    WARNING parse: %s" % ex)
    return found


def date_range(start_str, end_str):
    s = datetime.strptime(start_str, "%Y%m%d")
    e = datetime.strptime(end_str,   "%Y%m%d")
    out, cur = [], s
    while cur <= e:
        out.append(cur.strftime("%Y%m%d"))
        cur += timedelta(days=1)
    return out


def reconstruct_standings(bracket):
    """
    Rebuild group standings from stored result_X_Y entries.
    Returns (positions_dict, thirds_list).
    """
    positions = {}
    thirds    = []

    for letter, teams in GROUP_TEAMS.items():
        stats = {t: {"pts": 0, "gd": 0, "gf": 0, "gp": 0} for t in teams}

        for t1, t2 in combinations(teams, 2):
            key = rkey(t1, t2)
            if key not in bracket:
                continue
            s1, s2 = parse_score(bracket[key])
            if s1 is None:
                continue
            c1 = sorted([t1, t2])[0]
            t1_g = s1 if t1 == c1 else s2
            t2_g = s2 if t1 == c1 else s1

            stats[t1]["gp"] += 1
            stats[t2]["gp"] += 1
            stats[t1]["gf"] += t1_g
            stats[t2]["gf"] += t2_g
            stats[t1]["gd"] += t1_g - t2_g
            stats[t2]["gd"] += t2_g - t1_g

            if   t1_g > t2_g: stats[t1]["pts"] += 3
            elif t1_g < t2_g: stats[t2]["pts"] += 3
            else:              stats[t1]["pts"] += 1; stats[t2]["pts"] += 1

        played = sum(s["gp"] for s in stats.values()) // 2
        ranked = sorted(teams,
                        key=lambda t: (-stats[t]["pts"], -stats[t]["gd"], -stats[t]["gf"]))

        print("  Grupo %s: %d/6 partidos | %s" % (
            letter, played,
            " ".join("%s(%d)" % (t, stats[t]["pts"]) for t in ranked)))

        if played < 6:
            print("    -> grupo incompleto, esperando resultados")
            continue

        positions["1st_%s" % letter] = ranked[0]
        positions["2nd_%s" % letter] = ranked[1]
        thirds.append((ranked[2], letter,
                       stats[ranked[2]]["pts"],
                       stats[ranked[2]]["gd"],
                       stats[ranked[2]]["gf"]))
        print("    -> 1ro:%s  2do:%s  3ro:%s" % (ranked[0], ranked[1], ranked[2]))

    thirds.sort(key=lambda x: (-x[2], -x[3], -x[4]))
    return positions, thirds


def get_best3rd(groups_str, thirds):
    allowed = set(groups_str)
    for t in thirds:
        if t[1] in allowed:
            return t[0]
    return None


def resolve_r32(positions, thirds):
    bracket = {}
    for num, (s1, s2) in BRACKET_STRUCTURE.items():
        t1 = positions.get(s1)
        if t1 is None and "best3rd_" in s1:
            t1 = get_best3rd(s1.replace("best3rd_", ""), thirds)
        t2 = positions.get(s2)
        if t2 is None and "best3rd_" in s2:
            t2 = get_best3rd(s2.replace("best3rd_", ""), thirds)
        if t1: bracket["p%d_t1" % num] = t1
        if t2: bracket["p%d_t2" % num] = t2
    return bracket


def advance_knockout(bracket, results):
    winner_of = {}
    loser_of  = {}

    for num in range(73, 105):
        t1 = bracket.get("p%d_t1" % num, "")
        t2 = bracket.get("p%d_t2" % num, "")
        if not t1 or not t2:
            continue
        key = rkey(t1, t2)
        if key not in results:
            continue

        bracket[key] = results[key]
        s1, s2 = parse_score(results[key])
        if s1 is None:
            continue

        c1 = sorted([t1, t2])[0]
        t1_g = s1 if t1 == c1 else s2
        t2_g = s2 if t1 == c1 else s1

        if   t1_g > t2_g: winner_of[num], loser_of[num] = t1, t2
        elif t2_g > t1_g: winner_of[num], loser_of[num] = t2, t1
        else:              winner_of[num], loser_of[num] = t1, t2  # pen: keeper kept

        print("  P%d: %s %s %s -> avanza %s" % (num, t1, results[key], t2, winner_of[num]))

    for num, (f1, f2) in FEEDS.items():
        if f1 in winner_of: bracket["p%d_t1" % num] = winner_of[f1]
        if f2 in winner_of: bracket["p%d_t2" % num] = winner_of[f2]

    if 101 in loser_of: bracket["p103_t1"] = loser_of[101]
    if 102 in loser_of: bracket["p103_t2"] = loser_of[102]

    return bracket


def main():
    now = datetime.utcnow()
    print("\n" + "=" * 50)
    print("Mundial 2026 - %s UTC" % now.strftime("%Y-%m-%d %H:%M"))
    print("=" * 50 + "\n")

    # Cargar bracket existente
    bracket = {}
    if os.path.exists("bracket.json"):
        with open("bracket.json") as f:
            bracket = json.load(f)
    print("bracket.json existente: %d entradas" % len(bracket))

    # --- A. Resultados de fase de grupos (11-27 Jun) ---
    group_results_count = sum(
        1 for k in bracket
        if k.startswith("result_") and
        any(t in k for grp in GROUP_TEAMS.values() for t in grp)
    )
    print("\n--- A. Resultados de grupos (%d/72 en cache) ---" % group_results_count)

    if group_results_count < 72:
        group_dates = date_range("20260611", "20260627")
        # Fetch en bloques de 3 dias para no saturar ESPN
        for i in range(0, len(group_dates), 3):
            chunk = group_dates[i:i+3]
            print("  Fetching dias: %s" % ", ".join(chunk))
            new = fetch_results(chunk)
            bracket.update(new)
            print("  -> %d nuevos resultados" % len(new))
    else:
        print("  OK - todos los resultados de grupos en cache")

    # --- B. Reconstruir standings desde resultados ---
    print("\n--- B. Reconstruyendo standings desde resultados ---")
    positions, thirds = reconstruct_standings(bracket)
    print("\n  Posiciones calculadas: %d" % len(positions))
    print("  Mejores terceros: %s" % [t[0] for t in thirds[:8]])

    if positions:
        r32 = resolve_r32(positions, thirds)
        print("\n--- C. Bracket R32: %d slots resueltos ---" % len(r32))
        for k, v in sorted(r32.items()):
            print("  %s: %s" % (k, v))
        bracket.update(r32)
    else:
        print("  WARN: sin posiciones - esperando que terminen todos los grupos")

    # --- D. Resultados eliminatorios ---
    ko_end   = now.strftime("%Y%m%d")
    ko_dates = date_range("20260628", ko_end)
    print("\n--- D. Resultados eliminatorios (%s -> %s) ---" % (ko_dates[0], ko_end))
    ko_results = fetch_results(ko_dates)
    if ko_results:
        bracket = advance_knockout(bracket, ko_results)
        print("  %d partidos eliminatorios con resultado" % len(ko_results))
    else:
        print("  Sin resultados eliminatorios aun")

    # --- E. Guardar bracket.json ---
    with open("bracket.json", "w") as f:
        json.dump(bracket, f, indent=2, ensure_ascii=False)
    print("\nOK bracket.json guardado: %d entradas" % len(bracket))

    # --- F. Regenerar ICS ---
    print("\n--- F. Regenerando mundial2026.ics ---")
    r = subprocess.run([sys.executable, "build_ics.py"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print("  OK ICS generado")
        if r.stdout.strip():
            print(r.stdout.strip())
    else:
        print("  ERROR:\n%s" % r.stderr)
        sys.exit(1)

    print("\nOK Listo!\n")


if __name__ == "__main__":
    main()
