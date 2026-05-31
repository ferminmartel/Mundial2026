"""
build_ics.py
Genera mundial2026.ics leyendo bracket.json para los equipos clasificados.
Se ejecuta desde update_calendar.py (o a mano).
"""
from datetime import datetime, timedelta

TEAMS = {
    "MEX":("México"), "RSA":("Sudáfrica"), "KOR":("Corea del Sur"), "CZE":("Chequia"),
    "CAN":("Canadá"), "BIH":("Bosnia y Herzegovina"), "USA":("Estados Unidos"), "PAR":("Paraguay"),
    "QAT":("Catar"), "SUI":("Suiza"), "BRA":("Brasil"), "MAR":("Marruecos"),
    "HAI":("Haití"), "SCO":("Escocia"), "AUS":("Australia"), "TUR":("Turquía"),
    "GER":("Alemania"), "CUW":("Curazao"), "NED":("Países Bajos"), "JPN":("Japón"),
    "CIV":("Costa de Marfil"), "ECU":("Ecuador"), "SWE":("Suecia"), "TUN":("Túnez"),
    "ESP":("España"), "CPV":("Cabo Verde"), "BEL":("Bélgica"), "EGY":("Egipto"),
    "IRN":("Irán"), "NZL":("Nueva Zelanda"), "KSA":("Arabia Saudita"), "URU":("Uruguay"),
    "FRA":("Francia"), "SEN":("Senegal"), "IRQ":("Irak"), "NOR":("Noruega"),
    "ARG":("Argentina"), "ALG":("Argelia"), "AUT":("Austria"), "JOR":("Jordania"),
    "POR":("Portugal"), "COD":("RD Congo"), "ENG":("Inglaterra"), "CRO":("Croacia"),
    "GHA":("Ghana"), "PAN":("Panamá"), "UZB":("Uzbekistán"), "COL":("Colombia"),
}

FLAGS = {
    "MEX":"🇲🇽","RSA":"🇿🇦","KOR":"🇰🇷","CZE":"🇨🇿","CAN":"🇨🇦","BIH":"🇧🇦",
    "USA":"🇺🇸","PAR":"🇵🇾","QAT":"🇶🇦","SUI":"🇨🇭","BRA":"🇧🇷","MAR":"🇲🇦",
    "HAI":"🇭🇹","SCO":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","AUS":"🇦🇺","TUR":"🇹🇷","GER":"🇩🇪","CUW":"🇨🇼",
    "NED":"🇳🇱","JPN":"🇯🇵","CIV":"🇨🇮","ECU":"🇪🇨","SWE":"🇸🇪","TUN":"🇹🇳",
    "ESP":"🇪🇸","CPV":"🇨🇻","BEL":"🇧🇪","EGY":"🇪🇬","IRN":"🇮🇷","NZL":"🇳🇿",
    "KSA":"🇸🇦","URU":"🇺🇾","FRA":"🇫🇷","SEN":"🇸🇳","IRQ":"🇮🇶","NOR":"🇳🇴",
    "ARG":"🇦🇷","ALG":"🇩🇿","AUT":"🇦🇹","JOR":"🇯🇴","POR":"🇵🇹","COD":"🇨🇩",
    "ENG":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","CRO":"🇭🇷","GHA":"🇬🇭","PAN":"🇵🇦","UZB":"🇺🇿","COL":"🇨🇴",
}

# (uid_suffix, date, time_et, t1, t2, venue, city, tz, stage, grp_or_num)
GROUP_MATCHES = [
    ("g001","2026-06-11","15:00","MEX","RSA","Estadio Azteca","Ciudad de México, México",-1,"Fase de Grupos","A"),
    ("g002","2026-06-11","22:00","KOR","CZE","Estadio Akron","Guadalajara, México",-1,"Fase de Grupos","A"),
    ("g003","2026-06-12","15:00","CAN","BIH","BMO Field","Toronto, Canadá",0,"Fase de Grupos","B"),
    ("g004","2026-06-12","21:00","USA","PAR","SoFi Stadium","Los Ángeles, EE.UU.",-3,"Fase de Grupos","D"),
    ("g005","2026-06-13","15:00","QAT","SUI","Levi's Stadium","Santa Clara, EE.UU.",-3,"Fase de Grupos","B"),
    ("g006","2026-06-13","18:00","BRA","MAR","MetLife Stadium","East Rutherford, EE.UU.",0,"Fase de Grupos","C"),
    ("g007","2026-06-13","21:00","HAI","SCO","Gillette Stadium","Foxborough, EE.UU.",0,"Fase de Grupos","C"),
    ("g008","2026-06-14","00:00","AUS","TUR","BC Place","Vancouver, Canadá",-3,"Fase de Grupos","D"),
    ("g009","2026-06-14","13:00","GER","CUW","NRG Stadium","Houston, EE.UU.",-1,"Fase de Grupos","E"),
    ("g010","2026-06-14","16:00","NED","JPN","AT&T Stadium","Arlington (Dallas), EE.UU.",-1,"Fase de Grupos","F"),
    ("g011","2026-06-14","19:00","CIV","ECU","Lincoln Financial Field","Filadelfia, EE.UU.",0,"Fase de Grupos","E"),
    ("g012","2026-06-14","22:00","SWE","TUN","Estadio BBVA","Monterrey, México",-1,"Fase de Grupos","F"),
    ("g013","2026-06-15","12:00","ESP","CPV","Mercedes-Benz Stadium","Atlanta, EE.UU.",0,"Fase de Grupos","H"),
    ("g014","2026-06-15","15:00","BEL","EGY","Lumen Field","Seattle, EE.UU.",-3,"Fase de Grupos","G"),
    ("g015","2026-06-15","18:00","KSA","URU","Hard Rock Stadium","Miami, EE.UU.",0,"Fase de Grupos","H"),
    ("g016","2026-06-15","21:00","IRN","NZL","SoFi Stadium","Los Ángeles, EE.UU.",-3,"Fase de Grupos","G"),
    ("g017","2026-06-16","15:00","FRA","SEN","MetLife Stadium","East Rutherford, EE.UU.",0,"Fase de Grupos","I"),
    ("g018","2026-06-16","18:00","IRQ","NOR","Gillette Stadium","Foxborough, EE.UU.",0,"Fase de Grupos","I"),
    ("g019","2026-06-16","21:00","ARG","ALG","Arrowhead Stadium","Kansas City, EE.UU.",-1,"Fase de Grupos","J"),
    ("g020","2026-06-17","00:00","AUT","JOR","Levi's Stadium","Santa Clara, EE.UU.",-3,"Fase de Grupos","J"),
    ("g021","2026-06-17","13:00","POR","COD","NRG Stadium","Houston, EE.UU.",-1,"Fase de Grupos","K"),
    ("g022","2026-06-17","16:00","ENG","CRO","AT&T Stadium","Arlington (Dallas), EE.UU.",-1,"Fase de Grupos","L"),
    ("g023","2026-06-17","19:00","GHA","PAN","BMO Field","Toronto, Canadá",0,"Fase de Grupos","L"),
    ("g024","2026-06-17","22:00","UZB","COL","Estadio Azteca","Ciudad de México, México",-1,"Fase de Grupos","K"),
    ("g025","2026-06-18","12:00","CZE","RSA","Mercedes-Benz Stadium","Atlanta, EE.UU.",0,"Fase de Grupos","A"),
    ("g026","2026-06-18","15:00","SUI","BIH","SoFi Stadium","Los Ángeles, EE.UU.",-3,"Fase de Grupos","B"),
    ("g027","2026-06-18","18:00","CAN","QAT","BC Place","Vancouver, Canadá",-3,"Fase de Grupos","B"),
    ("g028","2026-06-18","21:00","MEX","KOR","Estadio Akron","Guadalajara, México",-1,"Fase de Grupos","A"),
    ("g029","2026-06-19","15:00","USA","AUS","Lumen Field","Seattle, EE.UU.",-3,"Fase de Grupos","D"),
    ("g030","2026-06-19","18:00","SCO","MAR","Gillette Stadium","Foxborough, EE.UU.",0,"Fase de Grupos","C"),
    ("g031","2026-06-19","20:30","BRA","HAI","Lincoln Financial Field","Filadelfia, EE.UU.",0,"Fase de Grupos","C"),
    ("g032","2026-06-19","23:00","TUR","PAR","Levi's Stadium","Santa Clara, EE.UU.",-3,"Fase de Grupos","D"),
    ("g033","2026-06-20","13:00","NED","SWE","NRG Stadium","Houston, EE.UU.",-1,"Fase de Grupos","F"),
    ("g034","2026-06-20","16:00","GER","CIV","BMO Field","Toronto, Canadá",0,"Fase de Grupos","E"),
    ("g035","2026-06-20","20:00","ECU","CUW","Arrowhead Stadium","Kansas City, EE.UU.",-1,"Fase de Grupos","E"),
    ("g036","2026-06-21","00:00","TUN","JPN","Estadio BBVA","Monterrey, México",-1,"Fase de Grupos","F"),
    ("g037","2026-06-21","12:00","ESP","KSA","Mercedes-Benz Stadium","Atlanta, EE.UU.",0,"Fase de Grupos","H"),
    ("g038","2026-06-21","15:00","BEL","IRN","SoFi Stadium","Los Ángeles, EE.UU.",-3,"Fase de Grupos","G"),
    ("g039","2026-06-21","18:00","URU","CPV","Hard Rock Stadium","Miami, EE.UU.",0,"Fase de Grupos","H"),
    ("g040","2026-06-21","21:00","NZL","EGY","BC Place","Vancouver, Canadá",-3,"Fase de Grupos","G"),
    ("g041","2026-06-22","13:00","ARG","AUT","AT&T Stadium","Arlington (Dallas), EE.UU.",-1,"Fase de Grupos","J"),
    ("g042","2026-06-22","17:00","FRA","IRQ","Lincoln Financial Field","Filadelfia, EE.UU.",0,"Fase de Grupos","I"),
    ("g043","2026-06-22","20:00","NOR","SEN","MetLife Stadium","East Rutherford, EE.UU.",0,"Fase de Grupos","I"),
    ("g044","2026-06-22","23:00","JOR","ALG","Levi's Stadium","Santa Clara, EE.UU.",-3,"Fase de Grupos","J"),
    ("g045","2026-06-23","13:00","POR","UZB","NRG Stadium","Houston, EE.UU.",-1,"Fase de Grupos","K"),
    ("g046","2026-06-23","16:00","ENG","GHA","Gillette Stadium","Foxborough, EE.UU.",0,"Fase de Grupos","L"),
    ("g047","2026-06-23","19:00","PAN","CRO","BMO Field","Toronto, Canadá",0,"Fase de Grupos","L"),
    ("g048","2026-06-23","22:00","COL","COD","Estadio Akron","Guadalajara, México",-1,"Fase de Grupos","K"),
    ("g049","2026-06-24","15:00","SUI","CAN","BC Place","Vancouver, Canadá",-3,"Fase de Grupos","B"),
    ("g050","2026-06-24","15:00","BIH","QAT","Lumen Field","Seattle, EE.UU.",-3,"Fase de Grupos","B"),
    ("g051","2026-06-24","18:00","SCO","BRA","Hard Rock Stadium","Miami, EE.UU.",0,"Fase de Grupos","C"),
    ("g052","2026-06-24","18:00","MAR","HAI","Mercedes-Benz Stadium","Atlanta, EE.UU.",0,"Fase de Grupos","C"),
    ("g053","2026-06-24","21:00","CZE","MEX","Estadio Azteca","Ciudad de México, México",-1,"Fase de Grupos","A"),
    ("g054","2026-06-24","21:00","RSA","KOR","Estadio BBVA","Monterrey, México",-1,"Fase de Grupos","A"),
    ("g055","2026-06-25","16:00","CUW","CIV","Lincoln Financial Field","Filadelfia, EE.UU.",0,"Fase de Grupos","E"),
    ("g056","2026-06-25","16:00","ECU","GER","MetLife Stadium","East Rutherford, EE.UU.",0,"Fase de Grupos","E"),
    ("g057","2026-06-25","19:00","JPN","SWE","AT&T Stadium","Arlington (Dallas), EE.UU.",-1,"Fase de Grupos","F"),
    ("g058","2026-06-25","19:00","TUN","NED","Arrowhead Stadium","Kansas City, EE.UU.",-1,"Fase de Grupos","F"),
    ("g059","2026-06-25","22:00","TUR","USA","SoFi Stadium","Los Ángeles, EE.UU.",-3,"Fase de Grupos","D"),
    ("g060","2026-06-25","22:00","PAR","AUS","Levi's Stadium","Santa Clara, EE.UU.",-3,"Fase de Grupos","D"),
    ("g061","2026-06-26","15:00","NOR","FRA","Gillette Stadium","Foxborough, EE.UU.",0,"Fase de Grupos","I"),
    ("g062","2026-06-26","15:00","SEN","IRQ","BMO Field","Toronto, Canadá",0,"Fase de Grupos","I"),
    ("g063","2026-06-26","20:00","CPV","KSA","NRG Stadium","Houston, EE.UU.",-1,"Fase de Grupos","H"),
    ("g064","2026-06-26","20:00","URU","ESP","Estadio Akron","Guadalajara, México",-1,"Fase de Grupos","H"),
    ("g065","2026-06-26","23:00","EGY","IRN","Lumen Field","Seattle, EE.UU.",-3,"Fase de Grupos","G"),
    ("g066","2026-06-26","23:00","NZL","BEL","BC Place","Vancouver, Canadá",-3,"Fase de Grupos","G"),
    ("g067","2026-06-27","17:00","PAN","ENG","MetLife Stadium","East Rutherford, EE.UU.",0,"Fase de Grupos","L"),
    ("g068","2026-06-27","17:00","CRO","GHA","Lincoln Financial Field","Filadelfia, EE.UU.",0,"Fase de Grupos","L"),
    ("g069","2026-06-27","19:30","COL","POR","Hard Rock Stadium","Miami, EE.UU.",0,"Fase de Grupos","K"),
    ("g070","2026-06-27","19:30","COD","UZB","Mercedes-Benz Stadium","Atlanta, EE.UU.",0,"Fase de Grupos","K"),
    ("g071","2026-06-27","22:00","ALG","AUT","Arrowhead Stadium","Kansas City, EE.UU.",-1,"Fase de Grupos","J"),
    ("g072","2026-06-27","22:00","JOR","ARG","AT&T Stadium","Arlington (Dallas), EE.UU.",-1,"Fase de Grupos","J"),
]

# Knockout: (uid, date, time_et, bracket_key_1, bracket_key_2, venue, city, tz, stage, match_num)
KNOCKOUT_MATCHES = [
    ("k073","2026-06-28","15:00","73","SoFi Stadium","Los Ángeles, EE.UU.",-3,"Ronda de 32",73),
    ("k074","2026-06-29","16:30","74","Gillette Stadium","Foxborough, EE.UU.",0,"Ronda de 32",74),
    ("k075","2026-06-29","21:00","75","Estadio BBVA","Monterrey, México",-1,"Ronda de 32",75),
    ("k076","2026-06-29","13:00","76","NRG Stadium","Houston, EE.UU.",-1,"Ronda de 32",76),
    ("k077","2026-06-30","17:00","77","MetLife Stadium","East Rutherford, EE.UU.",0,"Ronda de 32",77),
    ("k078","2026-06-30","13:00","78","AT&T Stadium","Arlington (Dallas), EE.UU.",-1,"Ronda de 32",78),
    ("k079","2026-06-30","21:00","79","Estadio Azteca","Ciudad de México, México",-1,"Ronda de 32",79),
    ("k080","2026-07-01","12:00","80","Mercedes-Benz Stadium","Atlanta, EE.UU.",0,"Ronda de 32",80),
    ("k081","2026-07-01","20:00","81","Levi's Stadium","Santa Clara, EE.UU.",-3,"Ronda de 32",81),
    ("k082","2026-07-01","16:00","82","Lumen Field","Seattle, EE.UU.",-3,"Ronda de 32",82),
    ("k083","2026-07-02","19:00","83","BMO Field","Toronto, Canadá",0,"Ronda de 32",83),
    ("k084","2026-07-02","15:00","84","SoFi Stadium","Los Ángeles, EE.UU.",-3,"Ronda de 32",84),
    ("k085","2026-07-02","23:00","85","BC Place","Vancouver, Canadá",-3,"Ronda de 32",85),
    ("k086","2026-07-03","18:00","86","Hard Rock Stadium","Miami, EE.UU.",0,"Ronda de 32",86),
    ("k087","2026-07-03","21:30","87","Arrowhead Stadium","Kansas City, EE.UU.",-1,"Ronda de 32",87),
    ("k088","2026-07-03","14:00","88","AT&T Stadium","Arlington (Dallas), EE.UU.",-1,"Ronda de 32",88),
    ("k089","2026-07-04","17:00","89","Lincoln Financial Field","Filadelfia, EE.UU.",0,"Octavos de Final",89),
    ("k090","2026-07-04","13:00","90","NRG Stadium","Houston, EE.UU.",-1,"Octavos de Final",90),
    ("k091","2026-07-05","16:00","91","MetLife Stadium","East Rutherford, EE.UU.",0,"Octavos de Final",91),
    ("k092","2026-07-05","20:00","92","Estadio Azteca","Ciudad de México, México",-1,"Octavos de Final",92),
    ("k093","2026-07-06","15:00","93","AT&T Stadium","Arlington (Dallas), EE.UU.",-1,"Octavos de Final",93),
    ("k094","2026-07-06","20:00","94","Lumen Field","Seattle, EE.UU.",-3,"Octavos de Final",94),
    ("k095","2026-07-07","12:00","95","Mercedes-Benz Stadium","Atlanta, EE.UU.",0,"Octavos de Final",95),
    ("k096","2026-07-07","16:00","96","BC Place","Vancouver, Canadá",-3,"Octavos de Final",96),
    ("k097","2026-07-09","16:00","97","Gillette Stadium","Foxborough, EE.UU.",0,"Cuartos de Final",97),
    ("k098","2026-07-10","15:00","98","SoFi Stadium","Los Ángeles, EE.UU.",-3,"Cuartos de Final",98),
    ("k099","2026-07-11","17:00","99","Hard Rock Stadium","Miami, EE.UU.",0,"Cuartos de Final",99),
    ("k100","2026-07-11","21:00","100","Arrowhead Stadium","Kansas City, EE.UU.",-1,"Cuartos de Final",100),
    ("k101","2026-07-14","15:00","101","AT&T Stadium","Arlington (Dallas), EE.UU.",-1,"Semifinal",101),
    ("k102","2026-07-15","15:00","102","Mercedes-Benz Stadium","Atlanta, EE.UU.",0,"Semifinal",102),
    ("k103","2026-07-18","17:00","103","Hard Rock Stadium","Miami, EE.UU.",0,"Tercer Puesto",103),
    ("k104","2026-07-19","15:00","104","MetLife Stadium","East Rutherford, EE.UU.",0,"FINAL",104),
]

def parse_et(d, t):
    y,mo,day = map(int,d.split("-"))
    h,mi = map(int,t.split(":"))
    return datetime(y,mo,day,h,mi) + timedelta(hours=4)

def fmt_ics(dt): return dt.strftime("%Y%m%dT%H%M%SZ")
def fmt_t(dt): return dt.strftime("%H:%M")

def full_name(code):
    return TEAMS.get(code, code)

def flag(code):
    return FLAGS.get(code, "")

def tv_channels(t1, t2, stage):
    is_arg = "ARG" in (t1+t2) or "Argentina" in (t1+t2)
    if is_arg: return "📺 TyC Sports · TV Pública · Telefe · DirecTV Sports"
    if any(x in stage for x in ["Final","Semifinal","Cuartos","Octavos"]): return "📺 TyC Sports · Telefe · DirecTV Sports"
    big = ["BRA","FRA","ESP","GER","NED","POR","BEL","URU","MEX","ENG"]
    if any(x in (t1+t2) for x in big): return "📺 TyC Sports · DirecTV Sports"
    return "📺 DirecTV Sports"

def make_group_event(row, bracket=None):
    if bracket is None: bracket = {}
    uid, date, time_et, c1, c2, venue, city, tz, stage, grp = row
    utc = parse_et(date, time_et)
    art = utc - timedelta(hours=3)
    local = utc + timedelta(hours=(-4+tz))
    n1, n2 = full_name(c1), full_name(c2)
    f1, f2 = flag(c1), flag(c2)

    # Buscar resultado si ya se jugó
    result_str = bracket.get(f"result_{c1}_{c2}") or bracket.get(f"result_{c2}_{c1}")
    if result_str and bracket.get(f"result_{c2}_{c1}") and not bracket.get(f"result_{c1}_{c2}"):
        parts = result_str.split("-")
        result_str = f"{parts[1]}-{parts[0]}"

    if result_str:
        summary = f"{c1} {result_str} {c2} | Grupo {grp}"
    else:
        summary = f"{c1} vs {c2} | Grupo {grp}"

    is_arg = "ARG" in (c1 + c2)
    color = "#75AADB" if is_arg else None  # Celeste Argentina

    desc_parts = [f"{f1} {n1}  vs  {f2} {n2}", ""]
    if result_str:
        desc_parts += [f"⚽ Resultado final: {c1} {result_str} {c2}", ""]
    desc_parts += [
        f"🕐 Hora Argentina (ART): {fmt_t(art)}",
        f"🕐 Hora local ({city.split(',')[0]}): {fmt_t(local)}",
        "",
        f"🏟 {venue}",
        f"📍 {city}",
        f"🏆 {stage} - Grupo {grp}",
        "",
        tv_channels(c1, c2, stage),
        "",
        "─────────────────────",
        "Copa del Mundo FIFA 2026",
        "EE.UU. · México · Canadá | 11 jun – 19 jul 2026",
    ]
    desc = "\\n".join(desc_parts)
    return _event(uid, utc, summary, desc, venue, city, color=color)

def make_knockout_event(row, bracket):
    uid, date, time_et, bkey, venue, city, tz, stage, num = row
    utc = parse_et(date, time_et)
    art = utc - timedelta(hours=3)
    local = utc + timedelta(hours=(-4+tz))

    t1 = bracket.get(f"p{num}_t1", f"Partido {num} - Equipo 1")
    t2 = bracket.get(f"p{num}_t2", f"Partido {num} - Equipo 2")
    n1 = full_name(t1) if t1 in TEAMS else t1
    n2 = full_name(t2) if t2 in TEAMS else t2
    f1 = flag(t1) if t1 in TEAMS else ""
    f2 = flag(t2) if t2 in TEAMS else ""

    is_arg = "ARG" in (t1 + t2)
    color = "#75AADB" if is_arg else None  # Celeste Argentina

    summary = f"{t1} vs {t2} | {stage} P{num}"
    desc = "\\n".join([
        f"{f1} {n1}  vs  {f2} {n2}".strip(),
        "",
        f"🕐 Hora Argentina (ART): {fmt_t(art)}",
        f"🕐 Hora local ({city.split(',')[0]}): {fmt_t(local)}",
        "",
        f"🏟 {venue}",
        f"📍 {city}",
        f"🏆 {stage} - Partido {num}",
        "",
        tv_channels(t1, t2, stage),
        "",
        "─────────────────────",
        "Copa del Mundo FIFA 2026",
        "EE.UU. · México · Canadá | 11 jun – 19 jul 2026",
    ])
    return _event(uid, utc, summary, desc, venue, city, color=color)

def _event(uid, utc, summary, desc, venue, city, color=None):
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}@mundial2026.ferminmartel",
        f"DTSTART:{fmt_ics(utc)}",
        f"DTEND:{fmt_ics(utc+timedelta(hours=2))}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{desc}",
        f"LOCATION:{venue}\\, {city}",
    ]
    if color:
        lines.append(f"COLOR:{color}")
        lines.append(f"X-APPLE-CALENDAR-COLOR:{color}")
    lines.append("END:VEVENT")
    return "\r\n".join(lines)

def generate(bracket=None, output="mundial2026.ics"):
    if bracket is None:
        bracket = {}
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ferminmartel//Mundial2026//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:⚽ Mundial 2026",
        "X-WR-TIMEZONE:America/Argentina/Buenos_Aires",
        "X-WR-CALDESC:FIFA World Cup 2026 - Horario Argentina. Se actualiza automaticamente.",
    ]
    for row in GROUP_MATCHES:
        lines.append(make_group_event(row, bracket))
    for row in KNOCKOUT_MATCHES:
        lines.append(make_knockout_event(row, bracket))
    lines.append("END:VCALENDAR")
    content = "\r\n".join(lines)
    with open(output, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ ICS generado: {output} ({len(GROUP_MATCHES)+len(KNOCKOUT_MATCHES)} partidos)")

if __name__ == "__main__":
    import json, os
    bracket = {}
    if os.path.exists("bracket.json"):
        with open("bracket.json") as f:
            bracket = json.load(f)
    generate(bracket)
