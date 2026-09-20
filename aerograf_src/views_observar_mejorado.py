"""Vista Streamlit del nivel 1: observacion orbital."""

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from .orbital import elevacion
from .visibility import aristas_bipartito
from .visualization import (
    CHART_CONFIG, PT_COLORS, apply_geo_theme, apply_xy_theme, hex_rgba,
    scattergeo_fae, scattergeo_isl, scattergeo_regions, scattergeo_sats,
)


def _curva_bezier(x0, y0, x1, y1, n=24):
    """Curva de Bezier cubica horizontal (tipo hive/sankey) entre dos puntos.

    Sustituye la antigua polilinea de 3 puntos: una curva suave reduce el
    ruido visual y hace mas legible el cruce de decenas de aristas.
    """
    t = np.linspace(0, 1, n)
    cx0, cx1 = x0 + (x1 - x0) * 0.4, x0 + (x1 - x0) * 0.6
    x = (1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * cx0 + 3 * (1 - t) * t ** 2 * cx1 + t ** 3 * x1
    y = (1 - t) ** 3 * y0 + 3 * (1 - t) ** 2 * t * y0 + 3 * (1 - t) * t ** 2 * y1 + t ** 3 * y1
    return x, y


def render_tab1(sats, edges, constellation, regions, fae_points, min_elevation,
                show_isl, show_coverage, predata, time_offset):
    st.markdown("### ① NIVEL 1 — OBSERVAR")
    st.markdown(
        "<div style='background:linear-gradient(90deg,#001f17,#00100d);border-left:2px solid #00ff88;padding:10px 14px;margin:8px 0 18px;color:#b8ffe0;font-size:12px'>"
        "¿Qué satélites pasan sobre Ecuador? Explora su posición, cobertura regional y enlaces con puntos de referencia.</div>",
        unsafe_allow_html=True,
    )
    left, right = st.columns([3, 2])
    color = constellation["color"]

    with left:
        st.markdown("#### Mapa orbital en tiempo real")
        figure = go.Figure()
        if show_isl:
            figure.add_trace(scattergeo_isl(edges, color))
        figure.add_trace(scattergeo_sats(sats, color))
        if show_coverage:
            counts = {
                name: sum(
                    elevacion(region["lat"], region["lon"], sat["lat"], sat["lon"],
                              sat["alt_km"]) >= min_elevation
                    for sat in sats
                )
                for name, region in regions.items()
            }
            for trace in scattergeo_regions(regions, counts):
                figure.add_trace(trace)
        for trace in scattergeo_fae(fae_points):
            figure.add_trace(trace)
        apply_geo_theme(figure, height=500)
        st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)

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
            times = predata["nivel1"]["time_steps"]
            for name, region in regions.items():
                figure.add_trace(go.Scatter(
                    x=times, y=selected.get(name, []),
                    mode="lines", name=name,
                    line=dict(color=region["color"], width=2),
                    fill="tozeroy", fillcolor=hex_rgba(region["color"], 0.05),
                    hovertemplate="%{y} visibles · %{x} min<extra>%{fullData.name}</extra>",
                ))
            apply_xy_theme(figure, height=270, hovermode="x unified",
                           xaxis_title="min", yaxis_title="Satélites visibles")
            st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)

        visible_sats, bipartite_edges, id_map = aristas_bipartito(
            sats, fae_points, min_elevation,
        )
        st.divider()
        st.markdown("#### Grafo de visibilidad SAT ↔ Puntos de referencia")

        sat_count = len(visible_sats)
        point_count = len(fae_points)
        point_colors = PT_COLORS

        # Elevación máxima por satélite (mejor geometría de enlace observada).
        max_elevation_por_indice = {}
        for edge in bipartite_edges:
            idx = id_map[edge["si"]]
            max_elevation_por_indice[idx] = max(max_elevation_por_indice.get(idx, 0), edge["el"])

        # Reordenar satélites por elevación máxima descendente: el mejor
        # enlace queda arriba, facilitando la lectura del grafo (menos
        # cruces visuales percibidos y jerarquía clara de calidad).
        orden = sorted(range(sat_count), key=lambda i: -max_elevation_por_indice.get(i, 0))
        rango_visual = {idx_original: puesto for puesto, idx_original in enumerate(orden)}

        position = lambda index, total: 0.5 if total <= 1 else 0.05 + index * 0.9 / (total - 1)
        sat_y = [position(rango_visual[index], sat_count) for index in range(sat_count)]
        point_y = [position(index, point_count) for index in range(point_count)]

        bipartite = go.Figure()
        latencias = [edge["ms"] for edge in bipartite_edges]
        lat_min, lat_max = (min(latencias), max(latencias)) if latencias else (0, 1)
        rango_lat = max(lat_max - lat_min, 1e-6)

        # ── Filtro interactivo por punto de referencia ───────────────────────
        nombres_puntos = [p["nombre"] for p in fae_points]
        filtro_punto = st.selectbox(
            "🔍 Resaltar conexiones de punto:",
            ["Todos"] + nombres_puntos,
            key="filtro_punto_bipartite",
        )
        punto_seleccionado = (
            None if filtro_punto == "Todos"
            else nombres_puntos.index(filtro_punto)
        )

        leyenda_mostrada = set()
        for edge in bipartite_edges:
            sat_index = id_map[edge["si"]]
            point_index = edge["pi"]
            calidad = 1 - (edge["ms"] - lat_min) / rango_lat

            # Resaltado: si hay un punto seleccionado, atenuar los demás.
            if punto_seleccionado is not None and point_index != punto_seleccionado:
                opacidad = 0.04
                grosor = 0.4
            else:
                opacidad = 0.40 + calidad * 0.60
                grosor = 1.2 + calidad * 5.5  # más contraste que antes

            x_curva, y_curva = _curva_bezier(0.15, sat_y[sat_index], 0.85, point_y[point_index])
            mostrar_leyenda = point_index not in leyenda_mostrada
            leyenda_mostrada.add(point_index)
            bipartite.add_trace(go.Scatter(
                x=x_curva, y=y_curva, mode="lines",
                legendgroup=f"punto-{point_index}",
                showlegend=mostrar_leyenda,
                name=fae_points[point_index]["nombre"] if mostrar_leyenda else None,
                opacity=opacidad,
                line=dict(color=point_colors[point_index % len(point_colors)], width=grosor),
                hovertemplate=(f"SAT-{edge['si']:02d} → {fae_points[point_index]['nombre']}<br>"
                               f"Elevación: {edge['el']}° · Latencia: {edge['ms']} ms"
                               f"<br>Calidad enlace: {calidad*100:.0f}%<extra></extra>"),
            ))

        if visible_sats:
            # Tamaño de nodo satélite proporcional al número de enlaces activos.
            enlaces_por_sat = [
                sum(1 for e in bipartite_edges if id_map[e["si"]] == i)
                for i in range(sat_count)
            ]
            bipartite.add_trace(go.Scatter(
                x=[0.15] * sat_count, y=sat_y, mode="markers+text",
                text=[f"SAT-{i:02d}" for i in range(sat_count)],
                textposition="middle left",
                textfont=dict(
                    size=9,
                    # Resaltar etiqueta del sat conectado al punto seleccionado.
                    color=[
                        "#00ff88" if punto_seleccionado is not None and any(
                            id_map[e["si"]] == i and e["pi"] == punto_seleccionado
                            for e in bipartite_edges
                        ) else "#ffffff"
                        for i in range(sat_count)
                    ],
                ),
                name="Satélites", legendgroup="satelites", showlegend=False,
                marker=dict(
                    size=[10 + enlaces_por_sat[i] * 2 for i in range(sat_count)],
                    color=[max_elevation_por_indice.get(i, 25) for i in range(sat_count)],
                    colorscale="Plasma", cmin=20, cmax=90, showscale=True,
                    colorbar=dict(
                        title=dict(text="Elev. máx (°)", font=dict(size=10)),
                        x=1.12, len=0.75, thickness=14, tickfont=dict(size=9),
                    ),
                    line=dict(width=1.2, color="#00ff88"),
                    symbol="circle",
                ),
                customdata=[
                    [sat["lat"], sat["lon"], sat["alt_km"],
                     max_elevation_por_indice.get(i, 0), enlaces_por_sat[i]]
                    for i, sat in enumerate(visible_sats)
                ],
                hovertemplate=(
                    "<b>SAT-%{text}</b><br>"
                    "Lat: %{customdata[0]:.1f}° · Lon: %{customdata[1]:.1f}°<br>"
                    "Alt: %{customdata[2]:.0f} km<br>"
                    "Elev. máx: %{customdata[3]:.1f}°<br>"
                    "Enlaces activos: %{customdata[4]}<extra></extra>"
                ),
            ))

        connections = [sum(edge["pi"] == index for edge in bipartite_edges) for index in range(point_count)]
        bipartite.add_trace(go.Scatter(
            x=[0.85] * point_count, y=point_y, mode="markers+text",
            text=[point["id"] for point in fae_points], textposition="middle right",
            textfont=dict(
                size=11,
                color=[
                    "#ffcc00" if punto_seleccionado is not None and i == punto_seleccionado
                    else "#ffffff"
                    for i in range(point_count)
                ],
            ),
            name="Puntos de referencia",
            legendgroup="puntos", showlegend=False,
            marker=dict(
                size=[16 + 3 * value for value in connections],
                color=point_colors[:point_count], symbol="diamond",
                line=dict(
                    width=[3 if punto_seleccionado is not None and i == punto_seleccionado else 1
                           for i in range(point_count)],
                    color="#ffcc00",
                ),
            ),
            customdata=[[connections[i], fae_points[i]["nombre"]] for i in range(point_count)],
            hovertemplate="<b>%{text}</b><br>%{customdata[1]}<br>Enlaces: %{customdata[0]}<extra></extra>",
        ))

        # Anotación dinámica cuando hay filtro activo.
        annotations_extra = []
        if punto_seleccionado is not None:
            enlaces_activos = sum(1 for e in bipartite_edges if e["pi"] == punto_seleccionado)
            annotations_extra.append(dict(
                x=0.5, y=-0.06,
                text=f"● Mostrando {enlaces_activos} enlace(s) hacia {filtro_punto}",
                showarrow=False,
                font=dict(size=10, color="#ffcc00"),
                xref="paper", yref="paper",
            ))

        bipartite.update_layout(
            height=max(420, min(720, sat_count * 26 + 120)),
            paper_bgcolor="#000000", plot_bgcolor="#050505",
            font=dict(color="#ffffff", family="Courier New, monospace"),
            margin=dict(l=80, r=150, t=50, b=40),
            xaxis=dict(visible=False, range=[0, 1.25]),
            yaxis=dict(visible=False, range=[-0.05, 1.05]),
            hoverdistance=18,
            hovermode="closest",
            legend=dict(bgcolor="#0d0d0d", bordercolor="#2a2a2a", font=dict(size=9),
                        orientation="h", yanchor="bottom", y=1.08, x=0,
                        title=dict(text="Punto → color de arista  ")),
            annotations=[
                dict(x=0.15, y=1.15, text="SATÉLITES (tamaño = enlaces · color = elevación)",
                     showarrow=False, font=dict(size=10, color="#aaaaaa")),
                dict(x=0.85, y=1.15, text="PUNTOS DE REFERENCIA",
                     showarrow=False, font=dict(size=10, color="#aaaaaa")),
            ] + annotations_extra,
        )
        st.plotly_chart(bipartite, use_container_width=True, config=CHART_CONFIG)
        st.caption(f"Aristas: {len(bipartite_edges)} · Satélites: {len(visible_sats)} · Desplazamiento: {time_offset} min · "
                   "Color de arista = punto de referencia · Grosor/opacidad = calidad del enlace (mayor = menor latencia) · "
                   "Color de nodo satelital = elevación máxima observada")
