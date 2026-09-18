"""Vista Streamlit: Registro FAE (COE) vs AEROGRAF-E — validación de ventanas de paso."""

import datetime

import pandas as pd
import streamlit as st

from .orbital import elevacion, propagate
from .registro_fae import REGISTRO_FAE

HL_UTC_OFFSET_H = -5  # Ecuador continental: hora local (HL) = UTC-5


def _norad_de_tle(l1: str) -> str:
    """Extrae el identificador NORAD (catálogo) de la línea 1 del TLE."""
    return l1[2:7].strip()


def _parse_ventana_hl(fecha: str, ventana: str) -> tuple:
    """Convierte una ventana 'HH:MM-HH:MM' en hora local a un rango datetime UTC."""
    inicio_txt, fin_txt = (parte.strip() for parte in ventana.split("-"))
    anio, mes, dia = (int(parte) for parte in fecha.split("-"))
    tz_local = datetime.timezone(datetime.timedelta(hours=HL_UTC_OFFSET_H))

    def _a_utc(hora_txt: str) -> datetime.datetime:
        h, m = (int(parte) for parte in hora_txt.split(":"))
        local = datetime.datetime(anio, mes, dia, h, m, tzinfo=tz_local)
        return local.astimezone(datetime.timezone.utc)

    inicio = _a_utc(inicio_txt)
    fin = _a_utc(fin_txt)
    if fin < inicio:
        fin += datetime.timedelta(days=1)
    return inicio, fin


def _ventanas_predichas(l1: str, l2: str, dia: datetime.date,
                        lat: float, lon: float,
                        min_el: float = 5.0, paso_min: int = 1) -> list:
    """Escanea un día completo (UTC) y devuelve las ventanas SGP4 con elevación >= min_el."""
    tle = {"name": "SAT", "l1": l1, "l2": l2, "alt_km": 550.0, "inc": 53.0}
    inicio_dia = datetime.datetime(dia.year, dia.month, dia.day, tzinfo=datetime.timezone.utc)
    ventanas, actual = [], None
    for minuto in range(0, 24 * 60, paso_min):
        t = inicio_dia + datetime.timedelta(minutes=minuto)
        sat = propagate([tle], t)[0]
        el = elevacion(lat, lon, sat["lat"], sat["lon"], sat["alt_km"])
        if el >= min_el:
            actual = [t, t] if actual is None else [actual[0], t]
        elif actual is not None:
            ventanas.append(tuple(actual))
            actual = None
    if actual is not None:
        ventanas.append(tuple(actual))
    return ventanas


def _mejor_coincidencia(ventana_registro: tuple, ventanas_predichas: list):
    """Empareja la ventana registrada con la ventana SGP4 más cercana en inicio."""
    inicio_reg, _ = ventana_registro
    mejor, mejor_delta = None, None
    for inicio_pred, fin_pred in ventanas_predichas:
        delta = abs((inicio_pred - inicio_reg).total_seconds()) / 60
        if mejor_delta is None or delta < mejor_delta:
            mejor_delta, mejor = delta, (inicio_pred, fin_pred)
    return mejor, mejor_delta


def render_tab_validacion(tles_reales: list, punto_referencia: dict, min_el: float = 5.0):
    """Compara el registro del COE contra las ventanas de paso calculadas por AEROGRAF-E."""
    st.markdown("### 🛰 REGISTRO vs AEROGRAF-E")
    st.info(
        "**El Centro de Operaciones Espaciales registra qué activos están presentes y "
        "cuándo son visibles. AEROGRAF-E toma esa información orbital, la procesa mediante "
        "SGP4 y teoría de grafos, y la transforma en una representación dinámica que permite "
        "comprender cómo evoluciona el entorno aeroespacial sobre Ecuador.**"
    )
    st.caption(
        "Fuente del registro: Consolidado de seguimiento de activos espaciales del COE, "
        "semana del 05 al 11 de septiembre de 2026. Punto de referencia: "
        f"{punto_referencia.get('nombre', 'Ecuador')} "
        f"({punto_referencia['lat']:.2f}°, {punto_referencia['lon']:.2f}°)."
    )

    tles_por_norad = {}
    for tle in tles_reales:
        tles_por_norad.setdefault(_norad_de_tle(tle["l1"]), tle)

    if st.button("Calcular ventanas AEROGRAF-E (SGP4)", type="primary"):
        filas = []
        for registro in REGISTRO_FAE:
            tle = tles_por_norad.get(registro["norad"])
            if not tle:
                continue
            inicio_reg, fin_reg = _parse_ventana_hl(registro["fecha"], registro["pasos_visibles_hl"])
            ventanas = _ventanas_predichas(
                tle["l1"], tle["l2"], inicio_reg.date(),
                punto_referencia["lat"], punto_referencia["lon"], min_el,
            )
            mejor, delta_min = _mejor_coincidencia((inicio_reg, fin_reg), ventanas)
            filas.append({
                "Fecha": registro["fecha"],
                "Activo": registro["nombre"],
                "NORAD": registro["norad"],
                "Registro COE (HL)": registro["pasos_visibles_hl"],
                "Registro COE (UTC)": f"{inicio_reg:%H:%M}-{fin_reg:%H:%M}",
                "AEROGRAF-E (UTC)": f"{mejor[0]:%H:%M}-{mejor[1]:%H:%M}" if mejor else "sin paso ≥ umbral",
                "Δ inicio (min)": round(delta_min, 1) if delta_min is not None else None,
                "Estado COE": registro["estado"],
            })
        st.session_state["_validacion_filas"] = filas

    filas = st.session_state.get("_validacion_filas")
    if not filas:
        st.warning("Presione el botón para comparar el registro del COE contra las ventanas SGP4 de AEROGRAF-E.")
        return

    df = pd.DataFrame(filas)
    st.dataframe(df, use_container_width=True, hide_index=True)

    deltas = [fila["Δ inicio (min)"] for fila in filas if fila["Δ inicio (min)"] is not None]
    columnas = st.columns(3)
    columnas[0].metric("Pasos comparados", len(filas))
    columnas[1].metric("Desviación promedio (min)", f"{sum(deltas) / len(deltas):.1f}" if deltas else "—")
    columnas[2].metric("Sin coincidencia SGP4", sum(1 for fila in filas if fila["Δ inicio (min)"] is None))
