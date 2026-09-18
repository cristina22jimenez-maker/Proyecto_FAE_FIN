"""Datos reales/registrados para AEROGRAF-E.

Fuente: documento "CONSOLIDADO DE SEGUIMIENTO DE ACTIVOS ESPACIALES
SEMANA DEL 05 AL 11 DE SEPTIEMBRE DE 2026", Centro de Operaciones Espaciales.
Los datos se incorporan como registro histórico de referencia; no representan
seguimiento en tiempo real.

Este módulo no sustituye la propagación SGP4 del proyecto. Su primera función
es integrar el registro documental con la interfaz de AEROGRAF-E y permitir
una futura validación TLE/paso.
"""

from __future__ import annotations

import csv
import os
from collections import Counter

import pandas as pd
import streamlit as st


COLUMNAS_REQUERIDAS = [
    "fecha", "turno", "activo", "pais", "identificador_orbita", "norad",
    "frecuencia", "velocidad_km_s", "argumento_perigeo_deg", "perigeo_km",
    "apogeo_km", "altitud_km", "paso_inicio_hl", "paso_fin_hl",
    "estado", "tle1", "tle2"
]


@st.cache_data(show_spinner=False)
def cargar_activos(csv_path: str) -> pd.DataFrame:
    """Carga el CSV histórico y valida su estructura básica."""
    if not os.path.exists(csv_path):
        return pd.DataFrame(columns=COLUMNAS_REQUERIDAS)

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en activos_espaciales.csv: {faltantes}")

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    for col in ["norad", "identificador_orbita", "velocidad_km_s",
                "argumento_perigeo_deg", "perigeo_km", "apogeo_km", "altitud_km"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _minutos(hhmm: str):
    """Convierte HH:MM a minutos desde medianoche."""
    try:
        h, m = str(hhmm).strip().replace(" ", "").split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


def duracion_paso_min(inicio: str, fin: str):
    a, b = _minutos(inicio), _minutos(fin)
    if a is None or b is None:
        return None
    return b - a if b >= a else (24 * 60 - a) + b


def render_tab_datos_reales(df: pd.DataFrame):
    """Renderiza la pestaña 0: DATOS REALES."""
    st.markdown("## ⓪ DATOS REALES")
    st.caption(
        "Registro histórico de activos espaciales. "
        "Fuente documental: Centro de Operaciones Espaciales, 05–11 SEP 2026."
    )

    if df.empty:
        st.warning("No se encontró activos_espaciales.csv.")
        return

    # --- KPIs ---
    total_registros = len(df)
    activos_unicos = df["norad"].nunique()
    paises = df["pais"].nunique()
    pasos = df["paso_inicio_hl"].notna().sum()
    activos = (df["estado"].str.upper() == "ACTIVO").sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Registros", total_registros)
    c2.metric("Activos únicos", activos_unicos)
    c3.metric("Países", paises)
    c4.metric("Pasos registrados", pasos)
    c5.metric("Estado ACTIVO", activos)

    st.divider()

    # --- Mensaje de concientización ---
    st.markdown(
        """
        ### 🌎 ¿Qué ocurre sobre Ecuador?

        El entorno aeroespacial es dinámico: distintos activos espaciales
        aparecen en ventanas de paso diferentes a lo largo del tiempo.
        **AEROGRAF-E convierte este registro orbital en información visual**
        para observar, caracterizar y estudiar esa dinámica.
        """
    )

    # --- Filtros ---
    f1, f2, f3 = st.columns(3)

    fechas = sorted(df["fecha"].dropna().dt.date.unique())
    fecha_sel = f1.selectbox(
        "Fecha del registro",
        fechas,
        format_func=lambda x: x.strftime("%d/%m/%Y"),
    )

    activos_lista = ["Todos"] + sorted(df["activo"].dropna().unique().tolist())
    activo_sel = f2.selectbox("Activo espacial", activos_lista)

    estados = ["Todos"] + sorted(df["estado"].dropna().unique().tolist())
    estado_sel = f3.selectbox("Estado", estados)

    vista = df[df["fecha"].dt.date == fecha_sel].copy()
    if activo_sel != "Todos":
        vista = vista[vista["activo"] == activo_sel]
    if estado_sel != "Todos":
        vista = vista[vista["estado"] == estado_sel]

    # --- Línea temporal de pasos ---
    st.markdown("### 🕒 Ventanas de paso sobre Ecuador")

    if vista.empty:
        st.info("No hay registros con los filtros seleccionados.")
    else:
        timeline = vista[
            ["activo", "pais", "norad", "paso_inicio_hl", "paso_fin_hl", "estado"]
        ].copy()
        timeline["duracion_min"] = timeline.apply(
            lambda r: duracion_paso_min(r["paso_inicio_hl"], r["paso_fin_hl"]),
            axis=1,
        )
        timeline = timeline.sort_values("paso_inicio_hl")
        st.dataframe(timeline, use_container_width=True, hide_index=True)

    st.divider()

    # --- Detalle del TLE ---
    st.markdown("### 🛰️ TLE utilizado como referencia")

    if not vista.empty:
        opciones = [
            f"{r.activo} | NORAD {int(r.norad)} | {r.paso_inicio_hl}-{r.paso_fin_hl}"
            for r in vista.itertuples()
        ]
        idx = st.selectbox("Seleccione un registro", range(len(opciones)),
                           format_func=lambda i: opciones[i])
        r = vista.iloc[idx]

        a, b = st.columns([1, 2])
        with a:
            st.markdown(f"**Activo:** {r['activo']}")
            st.markdown(f"**País:** {r['pais']}")
            st.markdown(f"**NORAD:** {int(r['norad'])}")
            st.markdown(f"**Altitud reportada:** {r['altitud_km']:.2f} km")
            st.markdown(f"**Estado:** {r['estado']}")
        with b:
            st.code(f"{r['tle1']}\n{r['tle2']}", language="text")

    st.divider()

    # --- Resumen por activo ---
    st.markdown("### 📊 Presencia registrada durante la semana")

    resumen = (
        df.groupby(["activo", "pais", "norad"], as_index=False)
        .agg(
            registros=("activo", "size"),
            pasos=("paso_inicio_hl", "count"),
            altitud_promedio_km=("altitud_km", "mean"),
        )
        .sort_values(["registros", "pasos"], ascending=False)
    )
    st.dataframe(
        resumen.style.format({"altitud_promedio_km": "{:.1f}"}),
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "Importante: este módulo integra un registro histórico del documento "
        "proporcionado para el concurso. La pestaña no debe presentarse como "
        "seguimiento satelital en tiempo real."
    )
