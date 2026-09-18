"""Cliente ligero para la API REST V4 de KeepTrack.space.

Documentación: https://keeptrack.space/api · https://api.keeptrack.space/v4/docs

Uso previsto en AEROGRAF-E: reemplazar los TLE sintéticos por TLE reales
para overlay en el mapa orbital (tab OBSERVAR). No sustituye el pipeline
de métricas/predata, que sigue basado en escenarios sintéticos FCC.

Requiere una API key gratuita (https://keeptrack.space -> menú de usuario ->
"API Key"). Se lee de, en orden: parámetro explícito, st.secrets["KEEPTRACK_API_KEY"],
variable de entorno KEEPTRACK_API_KEY.
"""

from __future__ import annotations

import os

import requests
import streamlit as st

from aerograf_src.orbital import extract_tle_params

API_BASE = "https://api.keeptrack.space/v4"
DEMO_API_KEY = "kt_demo_00000000000000000000000000"  # 30 req/hora, solo para pruebas

# Prefijo de nombre en el catálogo KeepTrack por constelación del proyecto.
CONSTELACION_PREFIJOS = {
    "Starlink": "STARLINK",
    "OneWeb": "ONEWEB",
    "Kuiper": "KUIPER",
}


def resolve_api_key(api_key: str | None = None) -> str | None:
    """Resuelve la API key desde parámetro, st.secrets o entorno."""
    if api_key:
        return api_key
    try:
        secret = st.secrets.get("KEEPTRACK_API_KEY")
        if secret:
            return secret
    except Exception:
        pass
    return os.environ.get("KEEPTRACK_API_KEY")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_catalog_brief(api_key: str) -> list[dict]:
    """Descarga el catálogo completo en un solo request (/v4/sats/brief).

    Se cachea 1 hora: el catálogo de KeepTrack no se actualiza con más
    frecuencia y el patrón recomendado es "una sola llamada masiva".
    """
    response = requests.get(
        f"{API_BASE}/sats/brief",
        headers={"X-API-Key": api_key},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def filter_by_constellation(catalog: list[dict], constellation: str) -> list[dict]:
    """Filtra el catálogo por prefijo de nombre de la constelación."""
    prefix = CONSTELACION_PREFIJOS.get(constellation)
    if not prefix:
        return []
    return [
        entry for entry in catalog
        if str(entry.get("name", "")).upper().startswith(prefix)
    ]


def to_project_tles(entries: list[dict]) -> list[dict]:
    """Convierte entradas KeepTrack a los dicts {name,l1,l2,alt_km,inc}
    que usa el resto del proyecto (mismo formato que parse_tle_file)."""
    tles = []
    for entry in entries:
        l1, l2 = entry.get("tle1"), entry.get("tle2")
        if not l1 or not l2:
            continue
        tle = {"name": entry.get("name", "SAT"), "l1": l1, "l2": l2,
               "alt_km": 550.0, "inc": 53.0}
        inc, alt = extract_tle_params(tle)
        tle["inc"], tle["alt_km"] = inc, alt
        tles.append(tle)
    return tles


def get_real_tles(constellation: str, api_key: str | None = None) -> list[dict]:
    """Obtiene TLE reales de KeepTrack para una constelación del proyecto.

    Nunca lanza excepción: si falla (sin key, red, rate limit), retorna []
    para que el llamador pueda usar el TLE sintético como respaldo.
    """
    tles, _ = get_real_tles_with_status(constellation, api_key)
    return tles


def get_real_tles_with_status(constellation: str, api_key: str | None = None) -> tuple[list[dict], str | None]:
    """Como get_real_tles, pero además retorna un motivo de error legible
    (o None si todo salió bien) para mostrar diagnóstico en la interfaz."""
    key = resolve_api_key(api_key)
    if not key:
        return [], "No se configuró ninguna API key de KeepTrack."
    try:
        catalog = fetch_catalog_brief(key)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status in (401, 403):
            return [], "API key de KeepTrack inválida o sin permisos (401/403)."
        if status == 429:
            return [], "Límite de solicitudes de KeepTrack excedido (429). Espera unos minutos."
        return [], f"Error HTTP {status} al consultar KeepTrack."
    except requests.Timeout:
        return [], "KeepTrack no respondió a tiempo (timeout)."
    except requests.RequestException as exc:
        return [], f"No se pudo conectar con KeepTrack: {exc}"
    entries = filter_by_constellation(catalog, constellation)
    if not entries:
        return [], f"KeepTrack respondió, pero no hay satélites '{constellation}' en el catálogo."
    tles = to_project_tles(entries)
    if not tles:
        return [], f"Las entradas de '{constellation}' no traían TLE utilizable (posible objeto solo-OMM)."
    return tles, None
