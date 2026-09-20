"""Vista Streamlit del nivel 3: ICA e ICAT regional."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from .visualization import (
    CHART_CONFIG, ICA_COLORSCALE, PT_COLORS, THEME, apply_geo_theme,
    apply_xy_theme, colorbar, hex_rgba, scattergeo_fae,
)


def render_tab3(data, constellation_name, regions, fae_points, constellations):
    st.markdown("### ③ NIVEL 3 — CONCIENTIZAR")
    st.markdown(
        "<div style='background:linear-gradient(90deg,#211d00,#100e00);border-left:2px solid #ffcc00;padding:10px 14px;margin:8px 0 18px;color:#fff1b8;font-size:12px'>"
        "¿Qué tan complejo es el entorno por región? Compara ICA, ICAT y la cobertura de los puntos FAE.</div>",
        unsafe_allow_html=True,
    )
    regional = data.get("regiones", {})
    selected = [regional.get(name, {}).get(constellation_name, {})
                for name in regions]
    left, right = st.columns([3, 2])
    with left:
        st.markdown("#### Mapa ICA/ICAT por región")
        figure = go.Figure()
        icas = [values.get("ica", 0) for values in selected]
        figure.add_trace(go.Scattergeo(
            lat=[regions[name]["lat"] for name in regions],
            lon=[regions[name]["lon"] for name in regions],
            mode="markers+text",
            text=[f"{name}<br>{ica:.0f}" for name, ica in zip(regions, icas)],
            textposition="top center",
            textfont=dict(size=11, color="#ffffff"),
            marker=dict(
                size=[18 + ica * 0.22 for ica in icas],
                color=icas, colorscale=ICA_COLORSCALE, cmin=0, cmax=100,
                colorbar=colorbar("ICA"),
                line=dict(width=1.2, color="rgba(255,255,255,0.45)"),
            ),
            customdata=[[name, values.get("ica", 0), values.get("icat", 0)]
                        for name, values in zip(regions, selected)],
            hovertemplate=("<b>%{customdata[0]}</b><br>ICA %{customdata[1]:.1f}"
                           "<br>ICAT %{customdata[2]:.1f}<extra></extra>"),
            name="ICA regional",
        ))
        for trace in scattergeo_fae(fae_points, showlegend=False):
            figure.add_trace(trace)
        apply_geo_theme(figure, height=440)
        st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)
    with right:
        st.markdown("#### Radar ICA — todas las constelaciones")
        figure = go.Figure()
        names = list(regions)
        for name, config in constellations.items():
            values = [regional.get(region, {}).get(name, {}).get("ica", 0)
                      for region in names]
            figure.add_trace(go.Scatterpolar(
                r=values + [values[0]], theta=names + [names[0]],
                fill="toself", name=name,
                line=dict(color=config["color"], width=2.2),
                fillcolor=hex_rgba(config["color"], 0.14),
                hovertemplate="%{theta}: %{r:.1f}<extra>%{fullData.name}</extra>",
            ))
        figure.update_layout(
            **{key: value for key, value in THEME.items() if key not in ("xaxis", "yaxis")},
            polar=dict(
                bgcolor="#080808",
                radialaxis=dict(
                    visible=True, range=[0, 100], gridcolor="#222222",
                    tickfont=dict(size=9, color="#888888"),
                    linecolor="#333333",
                ),
                angularaxis=dict(
                    gridcolor="#222222",
                    tickfont=dict(size=10, color="#cccccc"),
                    linecolor="#333333",
                ),
            ),
            height=440, margin=dict(l=40, r=40, t=36, b=36),
            legend=dict(orientation="h", yanchor="bottom", y=1.08, x=0,
                        bgcolor="rgba(12,12,12,0.85)", font=dict(size=10)),
        )
        st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)
    rows = []
    for name in regions:
        row = {"Región": name}
        for cname in constellations:
            values = regional.get(name, {}).get(cname, {})
            row[f"ICA {cname}"] = values.get("ica", 0)
            row[f"ICAT {cname}"] = values.get("icat", 0)
        rows.append(row)
    st.dataframe(pd.DataFrame(rows).set_index("Región"), use_container_width=True)

    st.markdown("#### ICA comparativo por región")
    figure = go.Figure()
    for name, config in constellations.items():
        values = [regional.get(region, {}).get(name, {}).get("ica", 0)
                  for region in regions]
        figure.add_trace(go.Bar(
            name=name, x=list(regions), y=values,
            marker=dict(color=config["color"], line=dict(width=0),
                        opacity=0.92),
            text=[f"{value:.0f}" for value in values],
            textposition="outside", textfont=dict(size=10, color="#cccccc"),
            hovertemplate="%{x}<br>ICA %{y:.1f}<extra>%{fullData.name}</extra>",
        ))
    figure.add_hline(y=70, line_dash="dash", line_color="#ff5555",
                     line_width=1, annotation_text="Umbral operacional (70)",
                     annotation_font_color="#ff8888")
    apply_xy_theme(figure, height=380, barmode="group", bargap=0.28,
                   yaxis_title="ICA (%)", yaxis_range=[0, 118],
                   hovermode="x unified")
    st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)

    st.markdown("#### 🔥 Heatmap ICA — región × constelación")
    region_names = list(regions)
    constellation_names = list(constellations)

    # ── Paleta semáforo perceptualmente uniforme ─────────────────────────────
    COLORSCALE_ICA_MEJORADO = [
        [0.00, "#c0392b"],
        [0.25, "#e74c3c"],
        [0.40, "#e67e22"],
        [0.55, "#f1c40f"],
        [0.70, "#2ecc71"],
        [0.85, "#27ae60"],
        [1.00, "#1a5e35"],
    ]

    def _calidad_label(v: float) -> str:
        if v >= 80:   return "Excelente"
        if v >= 55:   return "Bueno"
        if v >= 35:   return "Regular"
        return "Bajo"

    def _mini_bar(v: float) -> str:
        b = int(round(v / 10))
        return "█" * b + "░" * (10 - b)

    import numpy as np
    z = [[regional.get(region, {}).get(cname, {}).get("ica", 0)
          for cname in constellation_names]
         for region in region_names]
    z_arr = [[regional.get(region, {}).get(cname, {}).get("ica", 0)
              for cname in constellation_names]
             for region in region_names]

    # Promedio por constelación para badge en eje X.
    promedios = {
        cname: float(sum(regional.get(r, {}).get(cname, {}).get("ica", 0)
                         for r in region_names) / max(len(region_names), 1))
        for cname in constellation_names
    }

    # Texto enriquecido: valor + mini-barra unicode.
    text_matrix = [
        [f"{z_arr[ri][ci]:.0f}%  {_mini_bar(z_arr[ri][ci])}"
         for ci in range(len(constellation_names))]
        for ri in range(len(region_names))
    ]

    # Tooltip enriquecido.
    hover_matrix = [
        [
            f"<b>{constellation_names[ci]}</b> · {region_names[ri]}<br>"
            f"ICA: <b>{z_arr[ri][ci]:.1f}%</b><br>"
            f"Calidad: <b>{_calidad_label(z_arr[ri][ci])}</b><br>"
            f"Promedio constelación: {promedios[constellation_names[ci]]:.1f}%"
            for ci in range(len(constellation_names))
        ]
        for ri in range(len(region_names))
    ]

    # Etiquetas eje X con promedio badge.
    xtick_labels = [
        f"{cname}  (x̄ {promedios[cname]:.0f}%)"
        for cname in constellation_names
    ]

    figure = go.Figure(go.Heatmap(
        z=z_arr,
        x=xtick_labels,
        y=region_names,
        text=text_matrix,
        hovertext=hover_matrix,
        hoverinfo="text",
        texttemplate="%{text}",
        textfont=dict(size=12, color="white", family="Courier New, monospace"),
        colorscale=COLORSCALE_ICA_MEJORADO,
        zmin=0, zmax=100,
        colorbar=dict(
            title=dict(text="ICA (%)", font=dict(size=11, color="#cccccc")),
            tickfont=dict(size=9, color="#aaaaaa"),
            thickness=16,
            len=0.85,
            tickvals=[0, 25, 50, 75, 100],
            ticktext=["0 — Nulo", "25 — Bajo", "50 — Regular", "75 — Bueno", "100 — Óptimo"],
            bgcolor="rgba(0,0,0,0)",
            bordercolor="#2a2a2a",
        ),
        xgap=4,
        ygap=4,
    ))
    apply_xy_theme(figure, height=360, margin=dict(l=110, r=130, t=40, b=20))
    figure.update_xaxes(showgrid=False, ticks="", side="top",
                        tickfont=dict(size=11, color="#cccccc"))
    figure.update_yaxes(showgrid=False, ticks="", autorange="reversed",
                        tickfont=dict(size=11, color="#cccccc"))
    st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)

    st.markdown("#### ICA en puntos FAE")
    point_columns = st.columns(len(fae_points))
    point_data = data.get("puntos_fae", {})
    for column, point in zip(point_columns, fae_points):
        with column:
            st.markdown(f"**{point['id']} — {point['nombre']}**")
            for name, config in constellations.items():
                values = point_data.get(point["id"], {}).get(name, {})
                st.metric(name, f"{values.get('ica', 0):.1f}%",
                          f"{values.get('vis_promedio', 0):.1f} sats")

    st.markdown("#### 📦 Distribución de latencia por punto FAE")
    figure = go.Figure()
    for i, point in enumerate(fae_points):
        serie = point_data.get(point["id"], {}).get(constellation_name, {}).get("serie_lat_ms", [])
        if not serie:
            continue
        color = PT_COLORS[i % len(PT_COLORS)]
        figure.add_trace(go.Box(
            y=serie, name=f"{point['id']}  {point['nombre']}",
            marker_color=color, line=dict(color=color),
            fillcolor=hex_rgba(color, 0.18),
            boxmean=True, boxpoints="outliers",
        ))
    apply_xy_theme(figure, height=400, yaxis_title="Latencia (ms)",
                   showlegend=False)
    st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)
