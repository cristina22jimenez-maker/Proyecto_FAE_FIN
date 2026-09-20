"""Vista Streamlit del nivel 2: grafo dinamico."""

import networkx as nx
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .graph import build_isl, ruta_origen_destino
from .orbital import haversine
from .visualization import (
    CHART_CONFIG, THEME, apply_geo_theme, colorbar,
    scattergeo_fae, scattergeo_isl,
)


def render_tab2(sats, constellation, regions, fae_points, metrics, predata,
                 constellations=None, ciudades=None):
    st.markdown(
        "<div style='background:rgba(0,170,255,.04);border-left:3px solid #00aaff;"
        "padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:16px'>"
        "<strong style='color:#00aaff;letter-spacing:2px'>② NIVEL 2 — CARACTERIZAR</strong><br>"
        "<span style='color:#aaaaaa;font-size:13px'>"
        "¿Cómo cambia la conectividad y estructura del grafo a lo largo del tiempo? "
        "Métricas de teoría de grafos aplicadas a la red satelital sobre Ecuador."
        "</span></div>",
        unsafe_allow_html=True,
    )
    left, right = st.columns([2, 3])
    with left:
        st.markdown("#### 📊 Métricas del grafo actual")
        for label, key in (
            ("Nodos (sats sobre EC)", "sats_ec"), ("Aristas ISL", "aristas"),
            ("Densidad del grafo", "densidad"), ("Componente gigante", "giant_size"),
            ("Grado promedio", "grado_promedio"),
            ("Clustering promedio", "clustering"),
            ("Latencia promedio (ms)", "avg_path_ms"),
            ("Componentes conexas", "componentes"),
        ):
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;
            padding:8px 0;border-bottom:1px solid #1a3a6a;font-size:13px'>
            <span style='color:#aaaaaa'>{label}</span>
            <strong style='color:#81c784'>{metrics.get(key, 0)}</strong></div>
            """, unsafe_allow_html=True)

        st.divider()
        density = metrics.get("densidad", 0)
        clustering = metrics.get("clustering", 0)
        st.markdown(f"""
        <div style='background:#0d0d0d;border:1px solid #81c784;
        border-radius:8px;padding:12px;font-size:12px;color:#ffffff'>
        <strong style='color:#81c784'>📌 Interpretación</strong><br><br>
        Densidad <strong>{density}</strong> →
        {'Red bien conectada' if density > 0.1 else 'Red dispersa (típico LEO)'}<br>
        Clustering <strong>{clustering}</strong> →
        {'Nodos forman triángulos' if clustering > 0.3 else 'Topología de cadena'}<br>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("#### 🕸️ Grafo ISL sobre Ecuador — proyección geográfica")
        center_lat, center_lon = -1.5, -78.0
        sats_ec = [sat for sat in sats if haversine(
            center_lat, center_lon, sat["lat"], sat["lon"],
        ) < 2800]
        _, edges = build_isl(sats_ec) if constellation["isl"] else ([], [])
        figure = go.Figure()
        if edges:
            figure.add_trace(scattergeo_isl(
                edges, constellation["color"], name="ISL",
                opacity=0.38, width=0.9,
            ))
        if sats_ec:
            graph = nx.Graph()
            for index in range(len(sats_ec)):
                graph.add_node(index)
            for edge in edges:
                node_a = edge.get("a", edge.get("i"))
                node_b = edge.get("b", edge.get("j"))
                if node_a is not None and node_b is not None:
                    graph.add_edge(node_a, node_b)
            degree = dict(graph.degree())
            names = [sat.get("name", f"SAT-{index:02d}") for index, sat in enumerate(sats_ec)]
            figure.add_trace(go.Scattergeo(
                lat=[sat["lat"] for sat in sats_ec],
                lon=[sat["lon"] for sat in sats_ec],
                mode="markers",
                marker=dict(
                    size=[7 + degree.get(index, 0) * 2.6 for index in range(len(sats_ec))],
                    color=[degree.get(index, 0) for index in range(len(sats_ec))],
                    colorscale="Turbo", cmin=0, cmax=max(4, max(degree.values(), default=4)),
                    colorbar=colorbar("Grado"),
                    opacity=0.92,
                    line=dict(width=0.5, color="rgba(255,255,255,0.45)"),
                ),
                name="Satélite (tamaño=grado)",
                text=names,
                customdata=[[degree.get(index, 0), sats_ec[index].get("alt_km", 0)]
                            for index in range(len(sats_ec))],
                hovertemplate=("<b>%{text}</b><br>Grado %{customdata[0]}"
                               "<br>Alt %{customdata[1]:.0f} km<extra></extra>"),
            ))
        for trace in scattergeo_fae(fae_points, showlegend=False):
            figure.add_trace(trace)
        apply_geo_theme(figure, height=440)
        st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)

    st.markdown("#### 📈 Evolución temporal de métricas del grafo (95 min)")
    if predata and "nivel2" in predata:
        figure = make_subplots(
            rows=2, cols=3,
            subplot_titles=("Nodos sobre Ecuador", "Aristas ISL", "Densidad",
                            "Clustering", "Comp. Gigante", "Latencia prom. (ms)"),
            vertical_spacing=0.18, horizontal_spacing=0.08,
        )
        metrics_to_plot = ["nodos", "aristas", "densidad", "clustering", "giant_size", "avg_path_ms"]
        positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]
        times = predata["nivel2"]["time_steps"]
        for cname, cfg in (constellations or {constellation["name"]: constellation}).items():
            series = predata["nivel2"]["metricas"].get(cname, [])
            for metric_name, (row, column) in zip(metrics_to_plot, positions):
                values = [item.get(metric_name, 0) for item in series]
                figure.add_trace(go.Scatter(
                    x=times, y=values, mode="lines", name=cname,
                    line=dict(color=cfg["color"], width=2),
                    showlegend=(metric_name == "nodos"),
                    hovertemplate="%{y:.2f} · %{x} min<extra>%{fullData.name}</extra>",
                ), row=row, col=column)
        figure.update_layout(
            **{k: v for k, v in THEME.items() if k not in ("xaxis", "yaxis")},
            height=440, margin=dict(l=44, r=16, t=56, b=36),
            legend=dict(bgcolor="rgba(12,12,12,0.85)", bordercolor="#1e1e1e",
                        font=dict(size=10), orientation="h",
                        yanchor="bottom", y=1.06, x=0),
            hovermode="x unified",
        )
        figure.update_xaxes(gridcolor="#1a1a1a", title_text="min",
                            tickfont=dict(color="#888888", size=9),
                            showspikes=True, spikecolor="#333333")
        figure.update_yaxes(gridcolor="#1a1a1a",
                            tickfont=dict(color="#888888", size=9))
        figure.update_annotations(font=dict(size=11, color="#cccccc"))
        st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)

    if ciudades:
        st.divider()
        st.markdown("#### 🔗 Ruta origen → satélites → destino (Dijkstra)")
        center_lat, center_lon = -1.5, -78.0
        sats_ec = [sat for sat in sats if haversine(
            center_lat, center_lon, sat["lat"], sat["lon"],
        ) < 2800]
        _, edges_ec = build_isl(sats_ec) if constellation["isl"] else ([], [])

        nombres = [c["nombre"] for c in ciudades]
        col_o, col_d, col_e, col_b = st.columns([2, 2, 1, 1])
        with col_o:
            origen_nombre = st.selectbox("Origen", nombres, index=0, key="ruta_origen")
        with col_d:
            destino_nombre = st.selectbox("Destino", nombres, index=min(1, len(nombres) - 1), key="ruta_destino")
        with col_e:
            min_el_ruta = st.slider("Elev. mín (°)", 5, 45, 10, 5, key="ruta_min_el")
        with col_b:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            calcular_ruta = st.button("CALCULAR RUTA", use_container_width=True)

        if calcular_ruta:
            origen = next(c for c in ciudades if c["nombre"] == origen_nombre)
            destino = next(c for c in ciudades if c["nombre"] == destino_nombre)
            if origen_nombre == destino_nombre:
                st.warning("Elige un origen y un destino distintos.")
            else:
                resultado = ruta_origen_destino(sats_ec, edges_ec, origen, destino, min_el_ruta)
                if resultado is None:
                    st.error(
                        f"No hay ruta satelital entre {origen_nombre} y {destino_nombre} "
                        "en este instante con esa elevación mínima (prueba otro momento o baja la elevación)."
                    )
                else:
                    st.success(" → ".join(resultado["path"]))
                    m1, m2 = st.columns(2)
                    m1.metric("Saltos", resultado["saltos"])
                    m2.metric("Latencia total (ms)", resultado["latencia_ms"])
