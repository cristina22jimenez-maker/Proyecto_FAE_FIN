"""
indices.py — Índices de Cobertura Aeroespacial (ICA / ICAT)
════════════════════════════════════════════════════════════
Calcula los índices propios del proyecto AEROGRAF-E:

    ICA  = Índice de Cobertura Aeroespacial
           Mide el porcentaje del tiempo con cobertura satelital adecuada.
           ICA = (sats_visibles_promedio / umbral) × 100

    ICAT = ICA ponderado por latencia
           Penaliza regiones con satélites lejanos (horizonte = alta latencia).
           ICAT = ICA × (1 − latencia_promedio / lat_ref)

Importa desde orbital.py y visibility.py — sin duplicar física.
"""

import datetime
from typing import Optional

try:
    from .orbital import propagate, latlon_to_ecef, dist3d, latency_ms
    from .visibility import sats_visibles
except ImportError:  # modo directo: archivo ejecutado desde la raíz
    from orbital import propagate, latlon_to_ecef, dist3d, latency_ms
    from visibility import sats_visibles

# ═══════════════════════════════════════════════════════════════════════════════
# PARÁMETROS DE REFERENCIA
# ═══════════════════════════════════════════════════════════════════════════════
ICA_UMBRAL_SATS = 15.0    # Satélites visibles que representan ICA = 100%
ICAT_LAT_REF_MS = 20.0    # Latencia de referencia para penalización ICAT (ms)
MIN_EL_DEFAULT  = 25.0    # Elevación mínima operacional (°)


# ═══════════════════════════════════════════════════════════════════════════════
# CÁLCULO DE ICA / ICAT
# ═══════════════════════════════════════════════════════════════════════════════
def calcular_ica(vis_promedio: float,
                 umbral: float = ICA_UMBRAL_SATS) -> float:
    """
    ICA = (satélites_visibles_promedio / umbral) × 100
    Limitado a [0, 100].
    """
    return round(min(100.0, (vis_promedio / umbral) * 100.0), 1)


def calcular_icat(ica: float,
                  lat_promedio_ms: Optional[float],
                  lat_ref: float = ICAT_LAT_REF_MS) -> float:
    """
    ICAT = ICA × (1 − latencia_promedio / lat_ref)
    Si no hay datos de latencia, ICAT = ICA.
    Limitado a [0, 100].
    """
    if lat_promedio_ms is None:
        return ica
    factor = max(0.0, 1.0 - lat_promedio_ms / lat_ref)
    return round(min(100.0, ica * factor), 1)


# ═══════════════════════════════════════════════════════════════════════════════
# ICA POR REGIÓN
# ═══════════════════════════════════════════════════════════════════════════════
def ica_region(tles: list, lat: float, lon: float,
               t0: datetime.datetime,
               time_steps: list,
               min_el: float = MIN_EL_DEFAULT) -> dict:
    """
    Calcula ICA e ICAT para una región geográfica.

    Propaga los TLEs en cada instante de time_steps y promedia
    el número de satélites visibles y la latencia mínima.

    Retorna dict:
        ica          : índice ICA (0–100)
        icat         : índice ICAT (0–100)
        vis_promedio : satélites visibles promedio
        lat_promedio : latencia mínima promedio (ms)
        serie_vis    : lista de n_vis por instante
        serie_lat    : lista de lat_min_ms por instante
    """
    serie_vis = []
    serie_lat = []

    for dt_min in time_steps:
        t    = t0 + datetime.timedelta(minutes=float(dt_min))
        sats = propagate(tles, t)
        vis  = sats_visibles(sats, lat, lon, min_el)
        serie_vis.append(len(vis))
        if vis:
            serie_lat.append(min(s["latencia_ms"] for s in vis))

    avg_vis = sum(serie_vis) / max(len(serie_vis), 1)
    avg_lat = (sum(serie_lat) / len(serie_lat)) if serie_lat else None

    ica  = calcular_ica(avg_vis)
    icat = calcular_icat(ica, avg_lat)

    return {
        "ica":          ica,
        "icat":         icat,
        "vis_promedio": round(avg_vis, 1),
        "lat_promedio": round(avg_lat, 2) if avg_lat else None,
        "serie_vis":    serie_vis,
        "serie_lat":    serie_lat,
    }


def ica_punto(tles: list, punto: dict,
              t0: datetime.datetime,
              time_steps: list,
              min_el: float = MIN_EL_DEFAULT) -> dict:
    """
    Calcula ICA para un punto FAE específico (mismo algoritmo que ica_region).
    punto debe tener claves: lat, lon, alt_m (opcional).
    """
    return ica_region(
        tles,
        lat=punto["lat"],
        lon=punto["lon"],
        t0=t0,
        time_steps=time_steps,
        min_el=min_el,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CÁLCULO MASIVO — TODAS LAS REGIONES Y CONSTELACIONES
# ═══════════════════════════════════════════════════════════════════════════════
def calcular_nivel3(constelaciones_tles: dict,
                    regiones: dict,
                    puntos_fae: list,
                    t0: datetime.datetime,
                    time_steps: list,
                    min_el: float = MIN_EL_DEFAULT) -> dict:
    """
    Calcula ICA/ICAT para todas las combinaciones región × constelación
    y para todos los puntos FAE.

    Parámetros:
        constelaciones_tles : {nombre_const: [lista de TLEs]}
        regiones            : {nombre_region: {lat, lon, ...}}
        puntos_fae          : [{id, nombre, lat, lon, alt_m}, ...]
        t0                  : tiempo base (datetime UTC)
        time_steps          : offsets en minutos

    Retorna:
        {
          "regiones":    {region: {const: {ica, icat, vis_promedio, lat_promedio}}},
          "puntos_fae":  {pid:    {const: {ica, vis_promedio}}},
        }
    """
    resultado = {"regiones": {}, "puntos_fae": {}}

    for cname, tles in constelaciones_tles.items():
        # Un solo propagate por instante, reutilizado para todas las
        # regiones y puntos FAE (antes se repetía por cada uno: O(n) -> O(1)
        # propagaciones extra, clave para catálogos reales con miles de sats).
        serie_vis_region = {rname: [] for rname in regiones}
        serie_lat_region = {rname: [] for rname in regiones}
        serie_vis_punto = {p["id"]: [] for p in puntos_fae}
        serie_lat_punto = {p["id"]: [] for p in puntos_fae}

        for dt_min in time_steps:
            t = t0 + datetime.timedelta(minutes=float(dt_min))
            sats = propagate(tles, t)
            for rname, rdata in regiones.items():
                vis = sats_visibles(sats, rdata["lat"], rdata["lon"], min_el)
                serie_vis_region[rname].append(len(vis))
                if vis:
                    serie_lat_region[rname].append(min(s["latencia_ms"] for s in vis))
            for p in puntos_fae:
                vis = sats_visibles(sats, p["lat"], p["lon"], min_el)
                serie_vis_punto[p["id"]].append(len(vis))
                if vis:
                    serie_lat_punto[p["id"]].append(min(s["latencia_ms"] for s in vis))

        for rname in regiones:
            serie_vis = serie_vis_region[rname]
            serie_lat = serie_lat_region[rname]
            avg_vis = sum(serie_vis) / max(len(serie_vis), 1)
            avg_lat = (sum(serie_lat) / len(serie_lat)) if serie_lat else None
            ica = calcular_ica(avg_vis)
            icat = calcular_icat(ica, avg_lat)
            resultado["regiones"].setdefault(rname, {})[cname] = {
                "ica":          ica,
                "icat":         icat,
                "vis_promedio": round(avg_vis, 1),
                "lat_promedio": round(avg_lat, 2) if avg_lat else None,
                "serie_lat_ms": serie_lat,
            }

        for p in puntos_fae:
            pid = p["id"]
            serie_vis = serie_vis_punto[pid]
            serie_lat = serie_lat_punto[pid]
            avg_vis = sum(serie_vis) / max(len(serie_vis), 1)
            resultado["puntos_fae"].setdefault(pid, {})[cname] = {
                "ica":          calcular_ica(avg_vis),
                "vis_promedio": round(avg_vis, 1),
                "serie_lat_ms": serie_lat,
            }

    return resultado

