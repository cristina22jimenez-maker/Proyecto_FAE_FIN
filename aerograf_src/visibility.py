"""
visibility.py — Visibilidad satelital y cálculos de cobertura
═════════════════════════════════════════════════════════════
Calcula qué satélites son visibles desde cada punto/región
y genera series temporales de visibilidad.

Importa SOLO desde orbital.py — sin duplicar física.
"""

import datetime
from typing import Optional

try:
    from .orbital import (
        elevacion, latlon_to_ecef, dist3d,
        latency_ms, propagate, gen_tles, haversine,
    )
except ImportError:  # modo directo: archivo ejecutado desde la raíz
    from orbital import (
        elevacion, latlon_to_ecef, dist3d,
        latency_ms, propagate, gen_tles, haversine,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# VISIBILIDAD INSTANTÁNEA
# ═══════════════════════════════════════════════════════════════════════════════
def sats_visibles(sats: list, lat: float, lon: float,
                  min_el: float = 25.0) -> list:
    """
    Filtra satélites visibles desde un punto (lat, lon).

    Retorna lista de satélites con elevación ≥ min_el, cada uno con
    campo adicional 'el' (elevación en °) y 'latencia_ms'.
    """
    result = []
    ec_punto = latlon_to_ecef(lat, lon)
    for s in sats:
        el = elevacion(lat, lon, s["lat"], s["lon"], s["alt_km"])
        if el >= min_el:
            d_km  = dist3d(ec_punto, s["ecef"])
            lat_ms = latency_ms(d_km)
            result.append({**s, "el": round(el, 2), "latencia_ms": round(lat_ms, 3)})
    return result


def mejor_satelite(sats_vis: list) -> Optional[dict]:
    """
    Retorna el satélite de mayor elevación (mejor geometría de enlace).
    None si la lista está vacía.
    """
    if not sats_vis:
        return None
    return max(sats_vis, key=lambda s: s["el"])


def latencia_minima_ms(sats_vis: list) -> Optional[float]:
    """Latencia mínima (ms) entre el punto y sus satélites visibles."""
    if not sats_vis:
        return None
    return min(s["latencia_ms"] for s in sats_vis)


# ═══════════════════════════════════════════════════════════════════════════════
# VENTANA DE VISIBILIDAD TEMPORAL
# ═══════════════════════════════════════════════════════════════════════════════
def serie_visibilidad(tles: list, lat: float, lon: float,
                      t0: datetime.datetime,
                      time_steps: list,
                      min_el: float = 25.0) -> list:
    """
    Calcula cuántos satélites son visibles en cada instante de time_steps.

    Parámetros:
        tles       : lista de TLEs a propagar
        lat, lon   : coordenadas del punto de observación (°)
        t0         : tiempo base (datetime UTC)
        time_steps : lista de offsets en minutos desde t0
        min_el     : elevación mínima operacional (°)

    Retorna lista de dicts {t: offset_min, n_vis: int, lat_min_ms: float|None}
    """
    resultado = []
    for dt_min in time_steps:
        t    = t0 + datetime.timedelta(minutes=float(dt_min))
        sats = propagate(tles, t)
        vis  = sats_visibles(sats, lat, lon, min_el)
        resultado.append({
            "t":          dt_min,
            "n_vis":      len(vis),
            "lat_min_ms": latencia_minima_ms(vis),
        })
    return resultado


def visibilidad_por_region(tles: list, regiones: dict,
                            t0: datetime.datetime,
                            time_steps: list,
                            min_el: float = 25.0) -> dict:
    """
    Calcula serie de visibilidad para múltiples regiones.

    Parámetros:
        regiones : dict {nombre: {lat, lon, ...}}

    Retorna:
        {nombre_region: [{"t":, "n_vis":, "lat_min_ms":}, ...]}
    """
    return {
        rname: serie_visibilidad(tles, rdata["lat"], rdata["lon"],
                                  t0, time_steps, min_el)
        for rname, rdata in regiones.items()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ARISTAS DE VISIBILIDAD PARA GRAFO BIPARTITO
# ═══════════════════════════════════════════════════════════════════════════════
def aristas_bipartito(sats: list, puntos: list,
                       min_el: float = 25.0) -> tuple:
    """
    Calcula las aristas activas entre satélites y puntos FAE.

    Retorna:
        (sats_visibles, aristas, id_map)

        sats_visibles : lista de satélites con al menos 1 conexión
        aristas       : lista de dicts {si, pi, el, ms}
                        si = índice en sats_visibles
                        pi = índice en puntos
        id_map        : dict {idx_original → idx_en_sats_visibles}
    """
    aristas  = []
    ids_vis  = set()

    for pi, p in enumerate(puntos):
        ec_p = latlon_to_ecef(p["lat"], p["lon"], p.get("alt_m", 0) / 1000)
        for si, s in enumerate(sats):
            el = elevacion(p["lat"], p["lon"], s["lat"], s["lon"], s["alt_km"])
            if el >= min_el:
                d_km = dist3d(ec_p, s["ecef"])
                aristas.append({
                    "si": si,
                    "pi": pi,
                    "el": round(el, 1),
                    "ms": round(latency_ms(d_km), 2),
                })
                ids_vis.add(si)

    sats_vis = [sats[i] for i in sorted(ids_vis)]
    id_map   = {old: new for new, old in enumerate(sorted(ids_vis))}
    return sats_vis, aristas, id_map
