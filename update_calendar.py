"""
update_calendar.py
==================
Fetchea resultados del Mundial 2026 desde la ESPN API,
actualiza bracket.json con los equipos clasificados y
regenera mundial2026.ics.

Corre automáticamente cada 6 horas via GitHub Actions.
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass

# ─────────────────────────────────────────────
# ESPN API – no requiere API key
# ─────────────────────────────────────────────
ESPN_STANDINGS = "https://site.api.espn.com/apis/v2/sports/soccer/FIFA.WORLD/standings?season=2026"
ESPN_SCOREBOARD_TPL = "https://site.api.espn.com/apis/site/v2/sports/soccer/FIFA.WORLD/scoreboard?dates={date}"
ESPN_GROUPS_DATES = "20260611-20260627"  # Fase de grupos completa

# Mapeo nombre ESPN → código de 3 letras
ESPN_NAME_MAP = {
    "Mexico": "MEX", "South Africa": "RSA", "South Korea": "KOR", "Korea Republic": "KOR",
    "Czech Republic": "CZE", "Czechia": "CZE", "Canada": "CAN",
    "Bosnia and Herzegovina": "BIH", "United States": "USA", "USA": "USA",
    "Paraguay": "PAR", "Qatar": "QAT", "Switzerland": "SUI", "Brazil": "BRA",
    "Morocco": "MAR", "Haiti": "HAI", "Scotland": "SCO", "Australia": "AUS",
    "Turkey": "TUR", "Türkiye": "TUR", "Germany": "GER", "Curacao": "CUW",
    "Netherlands": "NED", "Japan": "JPN", "Ivory Coast": "CIV", "Côte d'Ivoire": "CIV",
    "Ecuador": "ECU", "Sweden": "SWE", "Tunisia": "TUN", "Spain": "ESP",
    "Cape Verde": "CPV", "Belgium": "BEL", "Egypt": "EGY", "Iran": "IRN",
    "New Zealand": "NZL", "Saudi Arabia": "KSA", "Uruguay": "URU", "France": "FRA",
    "Senegal": "SEN", "Iraq": "IRQ", "Norway": "NOR", "Argentina": "ARG",
    "Algeria": "ALG", "Austria": "AUT", "Jordan": "JOR", "Portugal": "POR",
    "DR Congo": "COD", "Congo DR": "COD", "England": "ENG", "Croatia": "CRO",
    "Ghana": "GHA", "Panama": "PAN", "Uzbekistan": "UZB", "Colombia": "COL",
}

# Estructura fija del bracket de Ronda de 32 (según FIFA)
# Cada partido: (equipo1_descripcion, equipo2_descripcion)
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


def fetch_json(url):
    """Descarga JSON desde una URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠️  No se pudo obtener {url}: {e}")
        return None


def to_code(name):
    """Convierte nombre de país ESPN a código de 3 letras."""
    return ESPN_NAME_MAP.get(name, name[:3].upper())


def fetch_group_standings():
    """
    Retorna dict: { "A": [("ARG",pts,gd), ...sorted by position], ... }
    """
    print("📡 Fetching standings de ESPN...")
    data = fetch_json(ESPN_STANDINGS)
    if not data:
        return {}

    groups = {}
    try:
        for group in data.get("standings", {}).get("groups", []):
            grp_name = group.get("name", "").replace("Group ", "").strip()
            if not grp_name or len(grp_name) != 1:
                continue
            teams = []
            for entry in group.get("standings", {}).get("entries", []):
                team_name = entry.get("team", {}).get("displayName", "")
                code = to_code(team_name)
                stats = {s["name"]: s["value"] for s in entry.get("stats", [])}
                pts = int(stats.get("points", 0))
                gd = int(stats.get("pointDifferential", stats.get("goalDifference", 0)))
                gf = int(stats.get("pointsFor", stats.get("goalsScored", 0)))
                teams.append((code, pts, gd, gf))
            # Ordenar: más puntos → mejor diferencia → más goles
            teams.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
            groups[grp_name] = teams
            print(f"  Grupo {grp_name}: {[t[0] for t in teams]}")
    except Exception as e:
        print(f"  ⚠️  Error parseando standings: {e}")

    return groups


def fetch_group_results():
    """
    Retorna dict con resultados de fase de grupos:
    { ("MEX","RSA"): (1, 2), ... }  → (goles_equipo1, goles_equipo2)
    Solo partidos ya finalizados.
    """
    print("📡 Fetching resultados de fase de grupos...")
    results = {}
    url = ESPN_SCOREBOARD_TPL.format(date=ESPN_GROUPS_DATES)
    data = fetch_json(url)
    if not data:
        return results
    for event in data.get("events", []):
        try:
            comp = event["competitions"][0]
            status = comp["status"]["type"]["name"]
            if status != "STATUS_FINAL":
                continue
            competitors = comp["competitors"]
            h = competitors[0]
            a = competitors[1]
            h_code = to_code(h["team"]["displayName"])
            a_code = to_code(a["team"]["displayName"])
            h_score = int(h.get("score", 0))
            a_score = int(a.get("score", 0))
            key = tuple(sorted([h_code, a_code]))
            # Guardamos en orden: primer equipo del key → su score
            if key[0] == h_code:
                results[key] = (h_score, a_score)
            else:
                results[key] = (a_score, h_score)
            print(f"  {h_code} {h_score}-{a_score} {a_code}")
        except Exception:
            continue
    return results


def fetch_knockout_results():
    """
    Recorre fechas de la fase eliminatoria y retorna
    dict: { match_num: ("ganador_code", "perdedor_code") }
    Solo partidos ya jugados y con resultado.
    """
    print("📡 Fetching resultados eliminatorios...")
    results = {}

    # Fechas de cada ronda
    rounds = [
        # Ronda de 32
        ("20260628", "20260703"),
        # Octavos
        ("20260704", "20260707"),
        # Cuartos
        ("20260709", "20260711"),
        # Semis + Final
        ("20260714", "20260719"),
    ]

    for start, end in rounds:
        url = ESPN_SCOREBOARD_TPL.format(date=f"{start}-{end}")
        data = fetch_json(url)
        if not data:
            continue
        for event in data.get("events", []):
            try:
                comp = event["competitions"][0]
                status = comp["status"]["type"]["name"]
                if status != "STATUS_FINAL":
                    continue
                competitors = comp["competitors"]
                home = competitors[0]
                away = competitors[1]
                h_name = home["team"]["displayName"]
                a_name = away["team"]["displayName"]
                h_score = int(home.get("score", 0))
                a_score = int(away.get("score", 0))
                # Intentar extraer match number del nombre del evento
                evt_name = event.get("name", "")
                # No siempre es fácil mapear al número de partido...
                # Guardamos por fecha y equipos
                h_code = to_code(h_name)
                a_code = to_code(a_name)
                if h_score > a_score:
                    winner, loser = h_code, a_code
                elif a_score > h_score:
                    winner, loser = a_code, h_code
                else:
                    winner, loser = None, None  # penales – ESPN marca ganador diferente
                    # Buscar winner en penalties
                    for c in competitors:
                        if c.get("winner"):
                            winner = to_code(c["team"]["displayName"])
                    loser = a_code if winner == h_code else h_code

                key = tuple(sorted([h_code, a_code]))
                results[key] = (winner, loser)
            except Exception:
                continue

    return results


def resolve_bracket(groups, knockout_results):
    """
    Construye bracket.json combinando standings y resultados de partidos.
    Retorna dict listo para bracket.json.
    """
    bracket = {}

    # Posiciones en grupos
    positions = {}  # "1st_A" → "ARG", "2nd_A" → "MEX", etc.
    third_place = []  # lista de (code, pts, gd, gf, grupo)

    for grp, teams in groups.items():
        if len(teams) >= 1:
            positions[f"1st_{grp}"] = teams[0][0]
        if len(teams) >= 2:
            positions[f"2nd_{grp}"] = teams[1][0]
        if len(teams) >= 3:
            third_place.append((teams[2][0], teams[2][1], teams[2][2], teams[2][3], grp))

    # Mejor 8 terceros (ordenados)
    third_place.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
    best8_thirds = [t[0] for t in third_place[:8]]
    best8_groups = [t[4] for t in third_place[:8]]

    def get_best3rd(groups_str):
        """Retorna el mejor tercer puesto de los grupos especificados."""
        allowed = list(groups_str)
        for t in third_place:
            if t[4] in allowed:
                return t[0]
        return "Por definir"

    # Resolver Ronda de 32
    for match_num, (slot1, slot2) in BRACKET_STRUCTURE.items():
        t1 = positions.get(slot1) or get_best3rd(slot1.replace("best3rd_", ""))
        t2 = positions.get(slot2) or get_best3rd(slot2.replace("best3rd_", ""))
        if t1: bracket[f"p{match_num}_t1"] = t1
        if t2: bracket[f"p{match_num}_t2"] = t2

    # Resolver rondas siguientes usando knockout_results
    # Para cada partido desde 89 en adelante, buscamos al ganador
    # de los partidos que lo alimentan
    winner_of = {}  # match_num → winner_code
    for (key, (winner, loser)) in knockout_results.items():
        # Buscar qué partido corresponde a estos equipos
        for n in range(73, 105):
            t1 = bracket.get(f"p{n}_t1", "")
            t2 = bracket.get(f"p{n}_t2", "")
            if set([t1, t2]) == set(key):
                winner_of[n] = winner
                break

    # Octavos (89-96) dependen de ganadores de R32 (73-88)
    FEEDS = {
        89: (74, 77), 90: (73, 75), 91: (76, 78), 92: (79, 80),
        93: (83, 84), 94: (81, 82), 95: (86, 88), 96: (85, 87),
        97: (89, 90), 98: (93, 94), 99: (91, 92), 100: (95, 96),
        101: (97, 98), 102: (99, 100),
        103: None, 104: (101, 102),
    }
    for match_num, feeds in FEEDS.items():
        if feeds is None:
            continue
        f1, f2 = feeds
        if f1 in winner_of:
            bracket[f"p{match_num}_t1"] = winner_of[f1]
        if f2 in winner_of:
            bracket[f"p{match_num}_t2"] = winner_of[f2]

    # Tercer puesto: perdedores de semis
    loser_of = {}
    for (key, (winner, loser)) in knockout_results.items():
        for n in range(73, 105):
            t1 = bracket.get(f"p{n}_t1", "")
            t2 = bracket.get(f"p{n}_t2", "")
            if set([t1, t2]) == set(key):
                loser_of[n] = loser
                break
    if 101 in loser_of: bracket["p103_t1"] = loser_of[101]
    if 102 in loser_of: bracket["p103_t2"] = loser_of[102]

    return bracket


def main():
    print(f"\n{'='*50}")
    print(f"🔄 Actualizando calendario Mundial 2026")
    print(f"   {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}\n")

    # Cargar bracket existente
    existing = {}
    if os.path.exists("bracket.json"):
        with open("bracket.json") as f:
            existing = json.load(f)

    # Fetch data
    groups = fetch_group_standings()
    knockout_results = fetch_knockout_results()
    group_results = fetch_group_results()

    if not groups and not knockout_results and not group_results:
        print("\n⚠️  No se obtuvo data nueva. Regenerando ICS con bracket existente.")
        bracket = existing
    else:
        bracket = resolve_bracket(groups, knockout_results)
        # Preservar datos existentes si el API no devolvió algo nuevo
        for k, v in existing.items():
            if k not in bracket:
                bracket[k] = v

    # Guardar resultados de fase de grupos en bracket.json
    # Formato: "result_MEX_RSA": "1-2"
    for (c1, c2), (s1, s2) in group_results.items():
        bracket[f"result_{c1}_{c2}"] = f"{s1}-{s2}"

    # Guardar bracket.json
    with open("bracket.json", "w") as f:
        json.dump(bracket, f, indent=2, ensure_ascii=False)
    print(f"\n✅ bracket.json actualizado ({len(bracket)} entradas)")

    # Regenerar ICS
    print("📅 Regenerando mundial2026.ics...")
    result = subprocess.run([sys.executable, "build_ics.py"], capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print(f"❌ Error en build_ics.py: {result.stderr}")
        sys.exit(1)

    print("\n✅ Todo listo!")


if __name__ == "__main__":
    main()
