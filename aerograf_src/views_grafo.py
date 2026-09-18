"""Vista Streamlit del nivel 2: grafo dinamico."""

import networkx as nx
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .graph import build_isl
from .orbital import haversine
from .visualization import THEME, THEME_GEO, geo_layout


def render_tab2(sats, constellation, regions, fae_points, metrics, predata,
                 constellations=None):
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
        for edge in edges:
            width = 0.5 + edge.get("w_ms", edge.get("w", 1)) / 5
            figure.add_trace(go.Scattergeo(
                lat=[edge["lat_a"], edge["lat_b"], None] if "lat_a" in edge
                    else [edge["la"], edge["lb"], None],
                lon=[edge["lon_a"], edge["lon_b"], None] if "lon_a" in edge
                    else [edge["loa"], edge["lob"], None],
                mode="lines", line=dict(width=width, color=constellation["color"]),
                opacity=0.4, showlegend=False,
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
            sizes = [6 + degree.get(index, 0) * 3 for index in range(len(sats_ec))]
            figure.add_trace(go.Scattergeo(
                lat=[sat["lat"] for sat in sats_ec],
                lon=[sat["lon"] for sat in sats_ec], mode="markers",
                marker=dict(size=sizes, color=constellation["color"], opacity=0.8,
                            line=dict(width=0.5, color="white")),
                name="Satélite (tamaño=grado)",
                hovertemplate="Grado: %{text}<extra></extra>",
                text=[str(degree.get(index, 0)) for index in range(len(sats_ec))],
            ))
        for point in fae_points:
            figure.add_trace(go.Scattergeo(
                lat=[point["lat"]], lon=[point["lon"]], mode="markers+text",
                text=[point["id"]], textposition="top right",
                textfont=dict(size=11, color="#ff4444"),
                marker=dict(size=14, color="#ff4444", symbol="triangle-up"),
                name=point["nombre"], showlegend=False,
            ))
        figure.update_layout(**THEME_GEO, geo=geo_layout(), height=420,
                             margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(figure, use_container_width=True)

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
                    line=dict(color=cfg["color"], width=1.8),
                    showlegend=(metric_name == "nodos"),
                ), row=row, col=column)
        figure.update_layout(
            **{k: v for k, v in THEME.items() if k not in ("xaxis", "yaxis")},
            height=400, margin=dict(l=40, r=10, t=50, b=30),
            legend=dict(bgcolor="#0d0d0d", bordercolor="#2a2a2a",
                        font=dict(size=10), orientation="h",
                        yanchor="bottom", y=1.04, x=0),
        )
        figure.update_xaxes(gridcolor="#1a1a1a", title_text="min")
        st.plotly_chart(figure, use_container_width=True)
