"""
orbital.py — Física orbital, carga de TLEs y propagación SGP4
═══════════════════════════════════════════════════════════════
Contiene TODAS las funciones de física orbital del proyecto.
El resto de módulos importan desde aquí — sin duplicación.

Funciones públicas:
    ecef_to_latlon, latlon_to_ecef, dist3d, latency_ms,
    haversine, elevacion, gen_tles, propagate,
    parse_tle_file, find_tle_file, extract_tle_params
"""

import math
import os
import datetime

try:
    from sgp4.api import Satrec, jday
    SGP4_OK = True
except ImportError:
    SGP4_OK = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES FÍSICAS
# ═══════════════════════════════════════════════════════════════════════════════
RE_KM   = 6_371.0        # Radio terrestre medio (km)
GM_KM3  = 398_600.4418   # Constante gravitacional (km³/s²)
C_KM_S  = 299_792.458    # Velocidad de la luz en vacío (km/s)

# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSIONES GEOMÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════════
def ecef_to_latlon(x: float, y: float, z: float) -> tuple:
    """
    Convierte coordenadas ECEF (km) → (lat°, lon°, alt_km).
    Usa esfera perfecta (suficiente para LEO con error <0.3%).
    """
    r   = math.sqrt(x**2 + y**2 + z**2)
    lat = math.degrees(math.asin(z / r))
    lon = math.degrees(math.atan2(y, x))
    alt = r - RE_KM
    return lat, lon, alt


def latlon_to_ecef(lat: float, lon: float, alt_km: float = 0.0) -> tuple:
    """
    Convierte (lat°, lon°, alt_km) → coordenadas ECEF (km).
    """
    r   = RE_KM + alt_km
    phi = math.radians(lat)
    lam = math.radians(lon)
    x   = r * math.cos(phi) * math.cos(lam)
    y   = r * math.cos(phi) * math.sin(lam)
    z   = r * math.sin(phi)
    return x, y, z


def dist3d(r1: tuple, r2: tuple) -> float:
    """Distancia euclidiana 3D entre dos puntos ECEF (km)."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(r1, r2)))


def latency_ms(dist_km: float) -> float:
    """Latencia de propagación de señal (ms) = distancia / c."""
    return (dist_km / C_KM_S) * 1_000.0


def haversine(lat1: float, lon1: float,
              lat2: float, lon2: float) -> float:
    """
    Distancia entre dos puntos sobre la superficie terrestre (km).
    Fórmula de Haversine — precisa para cualquier distancia.
    """
    p1  = math.radians(lat1)
    p2  = math.radians(lat2)
    dp  = math.radians(lat2 - lat1)
    dl  = math.radians(lon2 - lon1)
    a   = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * RE_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def elevacion(clat: float, clon: float,
              slat: float, slon: float, salt: float) -> float:
    """
    Ángulo de elevación (°) de un satélite visto desde una estación.

    Parámetros:
        clat, clon : coordenadas de la estación terrestre (°)
        slat, slon : coordenadas del subsatellite point (°)
        salt       : altitud del satélite (km)

    Retorna:
        elevación en grados [-90, 90].
        Positivo → satélite sobre el horizonte.
        ≥ 25°   → cobertura operacional recomendada.
    """
    d   = 2 * RE_KM * math.asin(math.sqrt(
        math.sin(math.radians((slat - clat) / 2)) ** 2 +
        math.cos(math.radians(clat)) *
        math.cos(math.radians(slat)) *
        math.sin(math.radians((slon - clon) / 2)) ** 2
    ))
    rho = d / RE_KM
    if rho < 1e-6:
        return 90.0
    return math.degrees(
        math.atan2(math.cos(rho) - RE_KM / (RE_KM + salt),
                   math.sin(rho))
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GENERACIÓN DE TLEs SINTÉTICOS (parámetros FCC reales)
# ═══════════════════════════════════════════════════════════════════════════════
def gen_tles(cfg: dict) -> list:
    """
    Genera TLEs sintéticos para un shell orbital usando Walker-Delta.

    Parámetros del dict cfg:
        planes  : número de planos orbitales
        sats    : satélites por plano
        inc     : inclinación (°)
        alt_km  : altitud (km)
        base    : número NORAD base

    Retorna lista de dicts con claves: l1, l2, name, alt_km, inc
    """
    tles  = []
    r     = RE_KM + cfg["alt_km"]
    T_min = 2 * math.pi * math.sqrt(r ** 3 / GM_KM3) / 60.0
    n_rev = 1440.0 / T_min                       # rev/día

    for p in range(cfg["planes"]):
        raan = (p / cfg["planes"]) * 360.0       # RAAN distribuido uniformemente
        for s in range(cfg["sats"]):
            # Anomalía media con desface Walker-Delta
            M     = ((s / cfg["sats"]) * 360.0 +
                     (p / cfg["planes"]) * (360.0 / cfg["sats"])) % 360.0
            norad = cfg["base"] + p * cfg["sats"] + s
            name  = f"{cfg.get('prefix','SAT')}-{p:02d}-{s:02d}"

            l1 = (f"1 {norad:05d}U 19074A   "
                  f"24015.50000000  .00001500  00000-0  15000-3 0  9990")
            l2 = (f"2 {norad:05d} {cfg['inc']:8.4f} {raan:8.4f} "
                  f"0001000  90.0000 {M:8.4f} {n_rev:11.8f}00010")

            tles.append({
                "name":   name,
                "l1":     l1,
                "l2":     l2,
                "alt_km": float(cfg["alt_km"]),
                "inc":    float(cfg["inc"]),
            })
    return tles


# ═══════════════════════════════════════════════════════════════════════════════
# CARGA DE TLEs REALES
# ═══════════════════════════════════════════════════════════════════════════════
def parse_tle_file(filepath: str) -> list:
    """
    Parsea un archivo .tle estándar (3 líneas o 2 líneas por satélite).

    Formato 3 líneas:
        STARLINK-1007
        1 44713U ...
        2 44713  ...

    Formato 2 líneas (sin nombre):
        1 44713U ...
        2 44713  ...

    Retorna lista de dicts: name, l1, l2, alt_km (inicial), inc (inicial).
    Los valores reales de alt_km e inc se calculan con extract_tle_params().
    """
    tles = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            raw = [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        return []

    i = 0
    while i < len(raw):
        # Formato 3 líneas
        if (i + 2 < len(raw)
                and raw[i + 1].startswith("1 ")
                and raw[i + 2].startswith("2 ")):
            tle = {"name": raw[i], "l1": raw[i + 1], "l2": raw[i + 2],
                   "alt_km": 550.0, "inc": 53.0}
            inc, alt = extract_tle_params(tle)
            tle["inc"]    = inc
            tle["alt_km"] = alt
            tles.append(tle)
            i += 3
        # Formato 2 líneas
        elif (i + 1 < len(raw)
              and raw[i].startswith("1 ")
              and raw[i + 1].startswith("2 ")):
            tle = {"name": f"SAT-{len(tles):04d}",
                   "l1": raw[i], "l2": raw[i + 1],
                   "alt_km": 550.0, "inc": 53.0}
            inc, alt = extract_tle_params(tle)
            tle["inc"]    = inc
            tle["alt_km"] = alt
            tles.append(tle)
            i += 2
        else:
            i += 1
    return tles


def extract_tle_params(tle: dict) -> tuple:
    """
    Extrae (inclinación°, altitud_km) reales desde las líneas TLE.

    Línea 2 col  8-16 : inclinación (°)
    Línea 2 col 52-63 : movimiento medio (rev/día) → radio → altitud
    """
    try:
        l2  = tle["l2"]
        inc = float(l2[8:16].strip())
        n   = float(l2[52:63].strip())                  # rev/día
        n_si= n * 2 * math.pi / 86_400.0               # rad/s
        a   = (GM_KM3 / (n_si ** 2)) ** (1.0 / 3.0)   # radio orbital (km)
        alt = round(a - RE_KM, 1)
        return inc, max(200.0, min(2_000.0, alt))
    except Exception:
        return 53.0, 550.0


def find_tle_file(script_dir: str, filename: str = "starlink.tle") -> str | None:
    """
    Busca el archivo TLE en múltiples ubicaciones.
    Compatible con Windows, Mac y Linux.

    Orden de búsqueda:
        1. Mismo directorio del script
        2. Directorio de trabajo actual
        3. Carpeta del usuario (~/)
        4. Subdirectorios data/ y tles/
        5. Variantes de extensión (.txt, .TLE)

    Retorna la primera ruta válida encontrada o None.
    """
    base = os.path.splitext(filename)[0]
    candidates = [
        os.path.join(script_dir, filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.path.expanduser("~"), filename),
        os.path.join(script_dir, "data",  filename),
        os.path.join(script_dir, "tles",  filename),
    ]
    for d in [script_dir, os.getcwd()]:
        for ext in [".tle", ".txt", ".TLE"]:
            candidates.append(os.path.join(d, base + ext))

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# PROPAGADOR SGP4
# ═══════════════════════════════════════════════════════════════════════════════
def _gmst_rad(jd: float, fr: float) -> float:
    """Tiempo sideral medio de Greenwich (rad) para rotar TEME → ECEF."""
    jd_full = jd + fr
    t_ut1 = (jd_full - 2451545.0) / 36525.0
    gmst_deg = (280.46061837 + 360.98564736629 * (jd_full - 2451545.0)
                + 0.000387933 * t_ut1 * t_ut1 - (t_ut1 ** 3) / 38_710_000.0)
    return math.radians(gmst_deg % 360.0)


def propagate(tles: list, t: datetime.datetime) -> list:
    """
    Propaga una lista de TLEs al instante t (datetime UTC).

    SGP4 devuelve la posición en el marco inercial TEME; se rota por el
    tiempo sideral de Greenwich para obtener coordenadas ECEF (Tierra fija)
    antes de derivar lat/lon, indispensable para instantes alejados del "ahora".

    Retorna lista de dicts con:
        name, l1, l2, alt_km, inc,
        lat (°), lon (°), alt_km (real), ecef ([x,y,z] km), vel ([vx,vy,vz] km/s)

    Los TLEs que fallen SGP4 (código ≠ 0) son silenciosamente omitidos.
    """
    if not SGP4_OK:
        return []

    jd, fr = jday(t.year, t.month, t.day,
                  t.hour, t.minute,
                  t.second + t.microsecond / 1_000_000.0)
    gmst = _gmst_rad(jd, fr)
    cos_g, sin_g = math.cos(gmst), math.sin(gmst)
    sats = []
    for tle in tles:
        try:
            sat     = Satrec.twoline2rv(tle["l1"], tle["l2"])
            e, r, v = sat.sgp4(jd, fr)
            if e != 0:
                continue
            x_teme, y_teme, z_teme = r
            x =  x_teme * cos_g + y_teme * sin_g
            y = -x_teme * sin_g + y_teme * cos_g
            z =  z_teme
            lat, lon, alt = ecef_to_latlon(x, y, z)
            sats.append({
                **tle,
                "lat":    lat,
                "lon":    lon,
                "alt_km": alt,
                "ecef":   [x, y, z],
                "vel":    list(v),
            })
        except Exception:
            continue
    return sats
