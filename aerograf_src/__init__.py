"""
aerograf_src — Paquete de módulos científicos de AEROGRAF-E
═══════════════════════════════════════════════════════════
Estructura:
    orbital.py     — Física orbital, TLEs, propagación SGP4
    visibility.py  — Visibilidad satelital y cobertura
    graph.py       — Construcción y métricas del grafo ISL
    indices.py     — Índices ICA e ICAT
    visualization.py — Layouts y helpers de Plotly

El archivo principal aerograf_e.py importa desde aquí
y solo maneja la interfaz Streamlit.
"""

from .orbital     import (ecef_to_latlon, latlon_to_ecef, dist3d,
                           latency_ms, haversine, elevacion,
                           gen_tles, propagate,
                           parse_tle_file, find_tle_file, extract_tle_params,
                           RE_KM, GM_KM3, C_KM_S, SGP4_OK)

from .visibility  import (sats_visibles, mejor_satelite, latencia_minima_ms,
                           serie_visibilidad, visibilidad_por_region,
                           aristas_bipartito)

from .graph       import (build_isl, build_networkx, graph_metrics,
                           dijkstra, serie_metricas, ruta_origen_destino,
                           ISL_MAX_KM, ISL_K)

from .indices     import (calcular_ica, calcular_icat,
                           ica_region, ica_punto, calcular_nivel3,
                           ICA_UMBRAL_SATS, ICAT_LAT_REF_MS)

from .visualization import (
    geo_layout,
    hex_rgba,
    THEME,
    THEME_GEO,
    LEGEND_STYLE,
    COLOR_STARLINK,
    COLOR_ONEWEB,
    COLOR_KUIPER,
    PT_COLORS,
    PT_SYMBOLS,
)
from .config import CONSTELACIONES, PUNTOS_FAE, REGIONES, TIME_STEPS, MODO_HISTORICO, REGION_CENTER, REGION_RADIUS_KM, CIUDADES_ECUADOR
from .passes import calcular_pasos
from .data import (
    cache_path,
    compute_graph_metrics,
    compute_all_levels,
    load_constellation_tles,
    load_precomputed,
    propagate_constellation,
    satellites_over_ecuador,
)
from .registro_fae import REGISTRO_FAE

__all__ = [
    # orbital
    "ecef_to_latlon","latlon_to_ecef","dist3d","latency_ms",
    "haversine","elevacion","gen_tles","propagate",
    "parse_tle_file","find_tle_file","extract_tle_params",
    "RE_KM","GM_KM3","C_KM_S","SGP4_OK",
    # visibility
    "sats_visibles","mejor_satelite","latencia_minima_ms",
    "serie_visibilidad","visibilidad_por_region","aristas_bipartito",
    # graph
    "build_isl","build_networkx","graph_metrics",
    "dijkstra","serie_metricas","ruta_origen_destino","ISL_MAX_KM","ISL_K",
    # indices
    "calcular_ica","calcular_icat","ica_region","ica_punto","calcular_nivel3",
    "ICA_UMBRAL_SATS","ICAT_LAT_REF_MS",
    # visualization
    "geo_layout","hex_rgba","THEME","THEME_GEO","LEGEND_STYLE",
    "COLOR_STARLINK","COLOR_ONEWEB","COLOR_KUIPER","PT_COLORS","PT_SYMBOLS",
    # config/data
    "CONSTELACIONES","PUNTOS_FAE","REGIONES","TIME_STEPS","MODO_HISTORICO",
    "REGION_CENTER","REGION_RADIUS_KM","CIUDADES_ECUADOR","calcular_pasos",
    "cache_path","compute_graph_metrics","compute_all_levels","load_constellation_tles",
    "load_precomputed","propagate_constellation","satellites_over_ecuador",
    # registro FAE
    "REGISTRO_FAE",
]
