"""Vista Streamlit de la pestaña DATOS ORBITALES.

Muestra el catalogo de TLE actualmente cargado (sintetico, KeepTrack o
CelesTrak) como tabla filtrable, sin recalcular posiciones ni grafos aqui:
esa es responsabilidad de las otras pestañas (OBSERVAR, CARACTERIZAR...).
"""

import pandas as pd
import streamlit as st


def _norad_id(l1: str) -> str:
    """Extrae el numero de catalogo NORAD de la linea 1 del TLE (col 3-7)."""
    try:
        return l1[2:7].strip()
    except Exception:
        return "?"


def render_tab_datos_orbitales(tles_by_constellation: dict, tle_source: dict,
                                last_update: str | None, data_source_label: str):
    st.markdown("### 🛰️ DATOS ORBITALES")
    st.markdown(
        "<div style='background:linear-gradient(90deg,#001f2e,#00100d);border-left:2px solid #4fc3f7;padding:10px 14px;margin:8px 0 18px;color:#b8e0ff;font-size:12px'>"
        "Catálogo de elementos orbitales actualmente cargado. La propagación SGP4, "
        "visibilidad y grafos se calculan localmente a partir de este catálogo — "
        "sin repetir llamadas a la API por cada cambio de la interfaz.</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox("Fuente", [data_source_label], disabled=True)
    with col2:
        categoria = st.selectbox("Categoría", list(tles_by_constellation), key="doc_categoria")
    with col3:
        busqueda = st.text_input("Búsqueda (nombre o NORAD)", key="doc_busqueda")

    tles = tles_by_constellation.get(categoria, [])
    rows = [{
        "Satélite": tle["name"],
        "NORAD": _norad_id(tle["l1"]),
        "Altitud (km)": round(tle["alt_km"], 1),
        "Inclinación (°)": round(tle["inc"], 2),
        "Fuente": tle_source.get(categoria, "synthetic"),
    } for tle in tles]
    df = pd.DataFrame(rows, columns=["Satélite", "NORAD", "Altitud (km)", "Inclinación (°)", "Fuente"])

    if busqueda:
        mask = (
            df["Satélite"].str.contains(busqueda, case=False, na=False)
            | df["NORAD"].str.contains(busqueda, case=False, na=False)
        )
        df = df[mask]

    st.divider()
    st.markdown("#### 📊 Resumen")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Satélites encontrados", len(df))
    m2.metric("Altitud promedio (km)", round(df["Altitud (km)"].mean(), 1) if len(df) else 0)
    m3.metric("Fuente de la categoría", tle_source.get(categoria, "synthetic"))
    m4.metric("Última actualización", last_update or "—")

    st.divider()
    st.dataframe(df, use_container_width=True, height=420)
