"""Preparacion y persistencia de datos para la interfaz Streamlit."""

import datetime
import json
import os

from .config import (
    CONSTELACIONES,
    PUNTOS_FAE,
    REGION_CENTER,
    REGION_RADIUS_KM,
    REGIONES,
    TIME_STEPS,
)
from .graph import serie_metricas
from .graph import build_isl, build_networkx, graph_metrics
from .indices import calcular_nivel3
from .orbital import gen_tles, haversine, propagate
from .visibility import sats_visibles


def cache_path(script_dir: str) -> str:
    """Devuelve la ruta del cache junto al script principal."""
    return os.path.join(os.path.abspath(script_dir), "aerograf_data_cache.json")


def satellites_over_ecuador(sats: list) -> list:
    """Filtra satelites dentro del radio de analisis de Ecuador."""
    clat, clon = REGION_CENTER
    return [
        sat for sat in sats
        if haversine(clat, clon, sat["lat"], sat["lon"]) < REGION_RADIUS_KM
    ]


def propagate_constellation(
    constellation: str,
    timestamp: datetime.datetime | None = None,
    time_offset_min: float = 0,
    script_dir: str = ".",
) -> list:
    """Genera y propaga una constelacion en un instante UTC."""
    if isinstance(timestamp, (int, float)):
        time_offset_min = timestamp
        timestamp = None
    timestamp = timestamp or datetime.datetime.now(datetime.timezone.utc)
    timestamp += datetime.timedelta(minutes=time_offset_min)
    tles = load_constellation_tles(constellation, script_dir)
    return propagate(tles, timestamp)


def load_constellation_tles(constellation: str, script_dir: str = ".") -> list:
    """Genera los TLE sintéticos definidos para una constelación."""
    return gen_tles(CONSTELACIONES[constellation])


def compute_graph_metrics(
    constellation: str,
    time_offset_min: float = 0,
    script_dir: str = ".",
    timestamp: datetime.datetime | None = None,
) -> dict:
    """Calcula las metricas instantaneas del grafo sobre Ecuador."""
    sats = satellites_over_ecuador(
        propagate_constellation(
            constellation,
            timestamp=timestamp,
            time_offset_min=time_offset_min,
            script_dir=script_dir,
        )
    )
    if not sats:
        return {}
    if CONSTELACIONES[constellation]["isl"]:
        _, edges = build_isl(sats)
    else:
        edges = []
    metrics = graph_metrics(build_networkx(sats, edges))
    return {**metrics, "sats_ec": len(sats)}


def compute_all_levels(
    t0: datetime.datetime | None = None,
    time_steps: list | None = None,
    script_dir: str = ".",
) -> dict:
    """Calcula los tres niveles de analisis para todas las constelaciones."""
    t0 = t0 or datetime.datetime.now(datetime.timezone.utc)
    time_steps = time_steps or TIME_STEPS
    tles_by_constellation = {
        name: load_constellation_tles(name, script_dir) for name in CONSTELACIONES
    }
    if any(not tles for tles in tles_by_constellation.values()):
        return {}

    nivel1 = {"time_steps": time_steps, "visibilidad": {}}
    for name, tles in tles_by_constellation.items():
        region_values = {region: [] for region in REGIONES}
        region_values["TOTAL"] = []
        for offset in time_steps:
            sats = propagate(tles, t0 + datetime.timedelta(minutes=offset))
            for region, point in REGIONES.items():
                region_values[region].append(
                    len(sats_visibles(sats, point["lat"], point["lon"]))
                )
            region_values["TOTAL"].append(
                len({
                    sat.get("l1", sat.get("name"))
                    for point in REGIONES.values()
                    for sat in sats_visibles(sats, point["lat"], point["lon"])
                })
            )
        nivel1["visibilidad"][name] = region_values

    nivel2 = {"time_steps": time_steps, "metricas": {}}
    for name, tles in tles_by_constellation.items():
        nivel2["metricas"][name] = serie_metricas(
            tles,
            t0,
            time_steps,
            region_center=REGION_CENTER,
            radio_km=REGION_RADIUS_KM,
            has_isl=CONSTELACIONES[name]["isl"],
        )

    nivel3 = calcular_nivel3(
        tles_by_constellation,
        REGIONES,
        PUNTOS_FAE,
        t0,
        time_steps,
    )
    return {
        "timestamp": t0.isoformat(),
        "tle_source": {
            name: "synthetic" for name in CONSTELACIONES
        },
        "regiones": REGIONES,
        "puntos_fae": PUNTOS_FAE,
        "nivel1": nivel1,
        "nivel2": nivel2,
        "nivel3": nivel3,
    }


def load_precomputed(
    script_dir: str = ".",
    calculate_if_missing: bool = True,
) -> dict:
    """Carga cache local y opcionalmente calcula el análisis histórico."""
    candidates = [
        cache_path(script_dir),
        os.path.join(os.path.expanduser("~"), "aerograf_data_cache.json"),
        "/tmp/aerograf_data.json",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as file:
                    cached = json.load(file)
                expected_sources = {
                    name: "synthetic"
                    for name in CONSTELACIONES
                }
                if cached.get("tle_source") == expected_sources:
                    return cached
            except (OSError, json.JSONDecodeError):
                continue

    if not calculate_if_missing:
        return {}

    result = compute_all_levels(script_dir=script_dir)
    try:
        with open(cache_path(script_dir), "w", encoding="utf-8") as file:
            json.dump(result, file)
    except OSError:
        pass
    return result
