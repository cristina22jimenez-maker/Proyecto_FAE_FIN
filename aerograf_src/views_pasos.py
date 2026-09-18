"""Vista Streamlit: PRÓXIMOS PASOS SOBRE ECUADOR (nivel 4)."""

import datetime

import streamlit as st
import plotly.graph_objects as go

from .orbital import propagate
from .passes import calcular_pasos
from .visualization import THEME_GEO, geo_layout

HORIZONTES = {
    "Próximas 6 horas": (360, 1),
    "Próximas 12 horas": (720, 2),
    "Próximas 24 horas": (1440, 4),
}


def render_tab_pasos(tles: list, ciudades: list, constellation_name: str, color: str):
    st.markdown("### 🛰️ PRÓXIMOS PASOS SOBRE ECUADOR")
    st.markdown(
        "<div style='background:linear-gradient(90deg,#1a0033,#00100d);border-left:2px solid #cc66ff;padding:10px 14px;margin:8px 0 18px;color:#e0c8ff;font-size:12px'>"
        "¿Qué activos espaciales son visibles desde diferentes puntos de Ecuador durante un periodo determinado?</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        punto_nombre = st.selectbox("Punto de referencia", [c["nombre"] for c in ciudades], key="pasos_punto_sel")
    with col2:
        min_el = st.slider("Elevación mínima (°)", 5, 60, 20, 5, key="pasos_el")
    with col3:
        horizonte_label = st.selectbox("Periodo", list(HORIZONTES), key="pasos_horizonte_sel")

    calcular = st.button("🔎 CALCULAR PASOS", use_container_width=True)

    if calcular:
        punto = next(c for c in ciudades if c["nombre"] == punto_nombre)
        horizonte_min, paso_min = HORIZONTES[horizonte_label]
        t0 = datetime.datetime.now(datetime.timezone.utc)
        with st.spinner(f"Calculando pasos de {constellation_name} sobre {punto_nombre}..."):
            pasos = calcular_pasos(tles, punto, t0, horizonte_min, paso_min, min_el)
        st.session_state["pasos_resultado"] = pasos
        st.session_state["pasos_punto_calc"] = punto
        st.session_state["pasos_t0"] = t0

    pasos = st.session_state.get("pasos_resultado")
    punto = st.session_state.get("pasos_punto_calc")
    t0 = st.session_state.get("pasos_t0")

    if pasos is None:
        st.info("Configura los parámetros y presiona CALCULAR PASOS.")
        return

    st.divider()
    if not pasos:
        st.warning(f"No se detectaron pasos de {constellation_name} sobre {punto['nombre']} con esos parámetros.")
        return

    st.markdown(f"#### {len(pasos)} pasos detectados sobre {punto['nombre']}")
    st.dataframe(
        [{
            "Satélite": p["satelite"], "Inicio": p["inicio"],
            "Máxima elevación": f"{p['elevacion_max']}°",
            "Fin": p["fin"], "Duración (min)": p["duracion_min"],
        } for p in pasos],
        use_container_width=True, height=360,
    )

    st.divider()
    st.markdown("#### 🗺️ Mapa del paso seleccionado")
    opciones = [f"{p['satelite']} · {p['inicio']}–{p['fin']} · {p['elevacion_max']}°" for p in pasos]
    elegido = st.selectbox("Selecciona un paso para ver su trayectoria", opciones, key="pasos_traj_sel")
    paso = pasos[opciones.index(elegido)]

    tle = next((t for t in tles if t.get("name") == paso["satelite"]), None)
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lat=[punto["lat"]], lon=[punto["lon"]], mode="markers+text",
        text=[punto["nombre"]], textposition="top center",
        marker=dict(size=14, color="#ff4444", symbol="triangle-up"),
        name=punto["nombre"],
    ))
    if tle is not None:
        muestras = max(2, int((paso["fin_min"] - paso["inicio_min"]) / 0.5) + 1)
        lats, lons = [], []
        for i in range(muestras):
            frac = i / (muestras - 1) if muestras > 1 else 0
            t_off = paso["inicio_min"] + frac * (paso["fin_min"] - paso["inicio_min"])
            sats = propagate([tle], t0 + datetime.timedelta(minutes=t_off))
            if sats:
                lats.append(sats[0]["lat"])
                lons.append(sats[0]["lon"])
        if lats:
            fig.add_trace(go.Scattergeo(
                lat=lats, lon=lons, mode="lines+markers",
                line=dict(width=2, color=color), marker=dict(size=5, color=color),
                name=f"Trayectoria {paso['satelite']}",
            ))
            fig.add_trace(go.Scattergeo(
                lat=[lats[0]], lon=[lons[0]], mode="markers", marker=dict(size=10, color="#00ff88"),
                name=f"Inicio ({paso['inicio']})",
            ))
            fig.add_trace(go.Scattergeo(
                lat=[lats[-1]], lon=[lons[-1]], mode="markers", marker=dict(size=10, color="#ffcc00"),
                name=f"Fin ({paso['fin']})",
            ))
    fig.update_layout(**THEME_GEO, geo=geo_layout(), height=420, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)
