"""Cliente ligero para el API publico GP (General Perturbations) de CelesTrak.

Documentacion: https://celestrak.org/NORAD/documentation/gp-data-formats.php
Consultas por GROUP (p. ej. starlink, oneweb) via https://celestrak.org/NORAD/elements/gp.php

No requiere API key, pero CelesTrak recomienda el mismo patron que KeepTrack:
descargar el catalogo por grupo y trabajar localmente en vez de repetir
consultas. Se cachea 1 hora con st.cache_data.

Limitacion conocida: CelesTrak esta migrando objetos nuevos a IDs NORAD de
6+ digitos (formato OMM/JSON), que el TLE clasico de 2 lineas no puede
representar. Este modulo usa FORMAT=tle, por lo que esos objetos nuevos
simplemente no apareceran hasta que el resto del proyecto (SGP4 con TLE)
migre a OMM.
"""

from __future__ import annotations

import requests
import streamlit as st

from aerograf_src.orbital import extract_tle_params

GP_URL = "https://celestrak.org/NORAD/elements/gp.php"

# Grupos GP de CelesTrak que existen hoy para cada constelacion del proyecto.
# Kuiper aun no tiene grupo propio en CelesTrak (constelacion en despliegue).
CONSTELACION_GRUPOS = {
    "Starlink": "starlink",
    "OneWeb": "oneweb",
    "Kuiper": "kuiper",
}


@st.cache_data(ttl=7200, show_spinner=False)
def fetch_group_tle(group: str) -> str:
    """Descarga un grupo GP completo en formato TLE (texto de 3 lineas).

    Cacheado 2h: CelesTrak actualiza cada grupo cada 2 horas y devuelve
    403 Forbidden si se repite la descarga del mismo grupo antes de eso
    (anti-scraping), con el motivo explicado en el cuerpo de la respuesta.
    """
    response = requests.get(GP_URL, params={"GROUP": group, "FORMAT": "tle"}, timeout=20)
    response.raise_for_status()
    return response.text


def parse_tle_text(raw: str) -> list[dict]:
    """Parsea texto TLE de 3 lineas (mismo formato que parse_tle_file, desde string)."""
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    tles = []
    i = 0
    while i + 2 < len(lines):
        if lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            tle = {"name": lines[i], "l1": lines[i + 1], "l2": lines[i + 2],
                   "alt_km": 550.0, "inc": 53.0}
            inc, alt = extract_tle_params(tle)
            tle["inc"], tle["alt_km"] = inc, alt
            tles.append(tle)
            i += 3
        else:
            i += 1
    return tles


def get_real_tles(constellation: str) -> list[dict]:
    """Obtiene TLE reales de CelesTrak para una constelacion del proyecto.

    Nunca lanza excepcion: retorna [] si el grupo no existe o falla la
    descarga, para que el llamador use el TLE sintetico como respaldo.
    """
    tles, _ = get_real_tles_with_status(constellation)
    return tles


def get_real_tles_with_status(constellation: str) -> tuple[list[dict], str | None]:
    """Como get_real_tles, pero ademas retorna un motivo de error legible
    (o None si todo salio bien) para mostrar diagnostico en la interfaz."""
    group = CONSTELACION_GRUPOS.get(constellation)
    if not group:
        return [], f"CelesTrak no tiene un grupo GP definido para '{constellation}'."
    try:
        raw = fetch_group_tle(group)
    except requests.HTTPError as exc:
        # CelesTrak explica el motivo del 403 (anti-repeticion, cada 2h) en el
        # cuerpo de la respuesta en texto plano; se lo mostramos tal cual.
        detail = exc.response.text.strip().splitlines()[0] if exc.response is not None and exc.response.text else str(exc)
        return [], f"CelesTrak rechazó la solicitud del grupo '{group}': {detail}"
    except requests.Timeout:
        return [], "CelesTrak no respondió a tiempo (timeout)."
    except requests.RequestException as exc:
        return [], f"No se pudo conectar con CelesTrak: {exc}"
    tles = parse_tle_text(raw)
    if not tles:
        return [], f"CelesTrak respondió, pero el grupo '{group}' vino vacío."
    return tles, None
