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
    z = [[regional.get(region, {}).get(cname, {}).get("ica", 0) for cname in constellation_names]
         for region in region_names]
    figure = go.Figure(go.Heatmap(
        z=z, x=constellation_names, y=region_names,
        colorscale=ICA_COLORSCALE, zmin=0, zmax=100,
        text=[[f"{value:.0f}" for value in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=13, color="#ffffff"),
        hovertemplate="%{y} · %{x}<br>ICA %{z:.1f}<extra></extra>",
        colorbar=colorbar("ICA (%)"),
        xgap=3, ygap=3,
    ))
    apply_xy_theme(figure, height=340, margin=dict(l=16, r=16, t=24, b=16))
    figure.update_xaxes(showgrid=False, ticks="", side="top")
    figure.update_yaxes(showgrid=False, ticks="", autorange="reversed")
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
