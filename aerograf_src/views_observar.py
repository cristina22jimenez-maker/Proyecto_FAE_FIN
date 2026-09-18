"""Vista Streamlit del nivel 1: observacion orbital."""

import streamlit as st
import plotly.graph_objects as go

from .orbital import elevacion
from .visibility import aristas_bipartito
from .visualization import THEME, THEME_GEO, geo_layout


def render_tab1(sats, edges, constellation, regions, fae_points, min_elevation,
                show_isl, show_coverage, predata, time_offset):
    st.markdown("### ① NIVEL 1 — OBSERVAR")
    st.markdown(
        "<div style='background:linear-gradient(90deg,#001f17,#00100d);border-left:2px solid #00ff88;padding:10px 14px;margin:8px 0 18px;color:#b8ffe0;font-size:12px'>"
        "¿Qué satélites pasan sobre Ecuador? Explora su posición, cobertura regional y enlaces con estaciones FAE.</div>",
        unsafe_allow_html=True,
    )
    left, right = st.columns([3, 2])
    color = constellation["color"]

    with left:
        st.markdown("#### Mapa orbital en tiempo real")
        figure = go.Figure(go.Scattergeo(
            lat=[sat["lat"] for sat in sats], lon=[sat["lon"] for sat in sats],
            mode="markers", marker=dict(size=5, color=color, opacity=0.6),
            name="Satélites",
        ))
        if show_isl:
            for edge in edges[:200]:
                figure.add_trace(go.Scattergeo(
                    lat=[edge["la"], edge["lb"], None],
                    lon=[edge["loa"], edge["lob"], None], mode="lines",
                    line=dict(width=0.5, color=color), opacity=0.2,
                    showlegend=False,
                ))
        if show_coverage:
            for name, region in regions.items():
                visible = [sat for sat in sats if elevacion(
                    region["lat"], region["lon"], sat["lat"], sat["lon"],
                    sat["alt_km"],
                ) >= min_elevation]
                figure.add_trace(go.Scattergeo(
                    lat=[region["lat"]], lon=[region["lon"]],
                    mode="markers+text", text=[f"{name} ({len(visible)})"],
                    textposition="top center", marker=dict(
                        size=14, color=region["color"], symbol="circle",
                    ), name=name,
                ))
        for point in fae_points:
            figure.add_trace(go.Scattergeo(
                lat=[point["lat"]], lon=[point["lon"]], mode="markers+text",
                text=[point["id"]], textposition="top right",
                marker=dict(size=12, color="#ff4444", symbol="triangle-up"),
                name=point["nombre"],
            ))
        figure.update_layout(**THEME_GEO, geo=geo_layout(), height=480,
                             margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(figure, use_container_width=True)

    with right:
        st.markdown("#### 👁️ Satélites visibles por región")
        for name, region in regions.items():
            count = sum(elevacion(
                region["lat"], region["lon"], sat["lat"], sat["lon"],
                sat["alt_km"],
            ) >= min_elevation for sat in sats)
            pct = min(100, count / 15 * 100)
            st.markdown(f"""
            <div style='margin-bottom:10px'>
              <div style='display:flex;justify-content:space-between;
              color:{region['color']};font-size:13px;font-weight:600'>
                <span>📍 {name}</span><span>{count} satélites</span>
              </div>
              <div style='background:#111111;border-radius:4px;height:8px;margin-top:4px'>
                <div style='background:{region['color']};width:{pct:.0f}%;
                height:100%;border-radius:4px'></div>
              </div>
              <div style='font-size:10px;color:#aaaaaa;margin-top:2px'>
                Cobertura: {pct:.0f}%
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.markdown("#### ⏱️ Visibilidad temporal (95 min)")
        if predata:
            figure = go.Figure()
            series = predata.get("nivel1", {}).get("visibilidad", {})
            selected = series.get(constellation["name"], {})
            for name, region in regions.items():
                figure.add_trace(go.Scatter(
                    x=predata["nivel1"]["time_steps"],
                    y=selected.get(name, []), mode="lines", name=name,
                    line=dict(color=region["color"], width=1.8),
                ))
            figure.update_layout(
                **THEME, height=250, margin=dict(l=40, r=10, t=10, b=30),
                xaxis_title="min", yaxis_title="Satélites visibles",
                legend=dict(bgcolor="#0d0d0d", bordercolor="#2a2a2a",
                            font=dict(size=9), orientation="h",
                            yanchor="bottom", y=1.02, xanchor="left", x=0),
            )
            st.plotly_chart(figure, use_container_width=True)

        visible_sats, bipartite_edges, id_map = aristas_bipartito(
            sats, fae_points, min_elevation,
        )
        st.divider()
        st.markdown("#### Grafo de visibilidad SAT ↔ FAE")
        point_colors = ["#ff3333", "#00aaff", "#00ff88", "#ffcc00"]
        sat_count = len(visible_sats)
        point_count = len(fae_points)
        position = lambda index, total: 0.5 if total <= 1 else 0.05 + index * 0.9 / (total - 1)
        sat_y = [position(index, sat_count) for index in range(sat_count)]
        point_y = [position(index, point_count) for index in range(point_count)]
        bipartite = go.Figure()
        max_latency = max((edge["ms"] for edge in bipartite_edges), default=1)
        for edge in bipartite_edges:
            sat_index = id_map[edge["si"]]
            point_index = edge["pi"]
            quality = 1 - edge["ms"] / max(max_latency, 1)
            middle = 0.5 + (point_y[point_index] - sat_y[sat_index]) * 0.08
            bipartite.add_trace(go.Scatter(
                x=[0.15, middle, 0.85],
                y=[sat_y[sat_index], (sat_y[sat_index] + point_y[point_index]) / 2, point_y[point_index]],
                mode="lines", showlegend=False,
                line=dict(color=point_colors[point_index % len(point_colors)], width=0.5 + quality * 3.5),
                hovertemplate=(f"SAT-{edge['si']:02d} → {fae_points[point_index]['nombre']}<br>"
                               f"Elevación: {edge['el']}° · Latencia: {edge['ms']} ms<extra></extra>"),
            ))
        if visible_sats:
            max_elevation = {}
            for edge in bipartite_edges:
                index = id_map[edge["si"]]
                max_elevation[index] = max(max_elevation.get(index, 0), edge["el"])
            bipartite.add_trace(go.Scatter(
                x=[0.15] * sat_count, y=sat_y, mode="markers+text",
                text=[f"SAT-{index:02d}" for index in range(sat_count)],
                textposition="middle left", name="Satélites",
                marker=dict(size=9, color=[max_elevation.get(i, 25) for i in range(sat_count)],
                            colorscale="Viridis", cmin=20, cmax=90),
                customdata=[[sat["lat"], sat["lon"], sat["alt_km"]] for sat in visible_sats],
                hovertemplate="Lat: %{customdata[0]:.1f}° · Lon: %{customdata[1]:.1f}°<br>Alt: %{customdata[2]:.0f} km<extra></extra>",
            ))
        connections = [sum(edge["pi"] == index for edge in bipartite_edges) for index in range(point_count)]
        bipartite.add_trace(go.Scatter(
            x=[0.85] * point_count, y=point_y, mode="markers+text",
            text=[point["id"] for point in fae_points], textposition="middle right",
            name="Puntos FAE", marker=dict(size=[14 + 2 * value for value in connections],
                                             color=point_colors[:point_count], symbol="diamond"),
            customdata=[[connections[index], fae_points[index]["nombre"]] for index in range(point_count)],
            hovertemplate="%{text}<br>Enlaces: %{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        ))
        bipartite.update_layout(
            height=max(400, min(700, sat_count * 24 + 100)),
            paper_bgcolor="#000000", plot_bgcolor="#050505",
            font=dict(color="#ffffff", family="Courier New, monospace"),
            margin=dict(l=80, r=180, t=35, b=20),
            xaxis=dict(visible=False, range=[0, 1.25]),
            yaxis=dict(visible=False, range=[-0.05, 1.05]),
            annotations=[
                dict(x=0.15, y=1.04, text="SATÉLITES", showarrow=False),
                dict(x=0.85, y=1.04, text="ESTACIONES FAE", showarrow=False),
            ],
        )
        st.plotly_chart(bipartite, use_container_width=True)
        st.caption(f"Aristas: {len(bipartite_edges)} · Satélites: {len(visible_sats)} · Desplazamiento: {time_offset} min")
