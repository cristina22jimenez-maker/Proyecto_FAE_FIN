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
    # Colores fijos según imagen de referencia
    BAR_COLORS = {
        "Starlink": "#2196f3",   # azul
        "OneWeb":   "#69f0ae",   # verde lima
        "Kuiper":   "#ffeb3b",   # amarillo
    }
    figure = go.Figure()
    for name, config in constellations.items():
        values = [regional.get(region, {}).get(name, {}).get("ica", 0)
                  for region in regions]
        bar_color = BAR_COLORS.get(name, config["color"])
        figure.add_trace(go.Bar(
            name=name, x=list(regions), y=values,
            marker=dict(color=bar_color, line=dict(width=0), opacity=1.0),
            text=[f"{value:.0f}" for value in values],
            textposition="outside",
            textfont=dict(size=11, color="#ffffff", family="sans-serif"),
            hovertemplate="%{x}<br>ICA %{y:.1f}<extra>%{fullData.name}</extra>",
        ))
    figure.add_hline(
        y=70, line_dash="dash", line_color="#ef5350", line_width=1.5,
        annotation_text="Umbral operacional (70)",
        annotation_font_color="#ef9a9a",
        annotation_position="top right",
    )
    figure.update_layout(
        title=dict(
            text="ICA comparativo por región",
            font=dict(size=13, color="#ffffff"), x=0, xanchor="left",
        ),
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        barmode="group", bargap=0.28, bargroupgap=0.05,
        height=400,
        margin=dict(l=60, r=30, t=50, b=60),
        font=dict(color="#cccccc"),
        legend=dict(
            orientation="v", x=1.01, y=1,
            bgcolor="rgba(0,0,0,0.6)",
            bordercolor="#444444", borderwidth=1,
            font=dict(size=13, color="#ffffff"),
        ),
        yaxis=dict(
            title=dict(text="ICA (%)", font=dict(size=13, color="#ffffff")),
            range=[0, 120],
            gridcolor="#2a2a2a", gridwidth=1, griddash="dot",
            zeroline=False,
            tickfont=dict(size=12, color="#ffffff"),
            tickcolor="#ffffff",
            linecolor="#444444", linewidth=1,
        ),
        xaxis=dict(
            gridcolor="#2a2a2a",
            tickfont=dict(size=12, color="#ffffff"),
            tickcolor="#ffffff",
            linecolor="#444444", linewidth=1,
        ),
        hovermode="x unified",
    )
    st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)

    st.markdown("#### 🔥 Heatmap ICA — región × constelación")
    region_names = list(regions)
    constellation_names = list(constellations)
    # Paleta verde → amarillo → rojo (igual a la imagen de referencia)
    HEATMAP_COLORSCALE = [
        [0.00, "#b71c1c"],   # rojo oscuro  → ICA muy bajo
        [0.20, "#e53935"],   # rojo
        [0.40, "#fdd835"],   # amarillo     → ICA medio
        [0.60, "#c8e6c9"],   # verde muy claro
        [0.80, "#43a047"],   # verde
        [1.00, "#1b5e20"],   # verde oscuro → ICA alto
    ]
    z = [[regional.get(region, {}).get(cname, {}).get("ica", 0)
          for cname in constellation_names]
         for region in region_names]
    figure = go.Figure(go.Heatmap(
        z=z,
        x=constellation_names,
        y=region_names,
        colorscale=HEATMAP_COLORSCALE,
        zmin=0, zmax=100,
        text=[[f"{value:.0f}" for value in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=14, color="#ffffff", family="sans-serif"),
        hovertemplate="%{y} · %{x}<br>ICA: <b>%{z:.1f}%</b><extra></extra>",
        colorbar=dict(
            title=dict(text="ICA (%)", font=dict(size=13, color="#ffffff")),
            tickfont=dict(size=12, color="#ffffff"),
            thickness=18, len=0.9,
            tickvals=[0, 25, 50, 75, 100],
            bgcolor="rgba(0,0,0,0)",
            bordercolor="#444444",
            borderwidth=1,
        ),
        xgap=2, ygap=2,
    ))
    figure.update_layout(
        title=dict(
            text="🔥 Heatmap ICA — región × constelación",
            font=dict(size=15, color="#ffffff", family="sans-serif"),
            x=0.0, xanchor="left",
        ),
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#ffffff"),
        height=380,
        margin=dict(l=120, r=110, t=60, b=50),
    )
    figure.update_xaxes(
        showgrid=False, ticks="outside", ticklen=5,
        side="bottom",
        tickfont=dict(size=13, color="#ffffff", family="sans-serif"),
        tickcolor="#ffffff",
        linecolor="#444444", linewidth=1,
    )
    figure.update_yaxes(
        showgrid=False, ticks="outside", ticklen=5,
        autorange="reversed",
        tickfont=dict(size=13, color="#ffffff", family="sans-serif"),
        tickcolor="#ffffff",
        linecolor="#444444", linewidth=1,
    )
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
    BOX_COLOR      = "#00897b"   # verde azulado de las cajas
    BOX_FILL       = "#00695c"   # relleno ligeramente más oscuro
    MEDIAN_COLOR   = "#ffffff"   # mediana blanca sólida
    MEAN_COLOR     = "#ffdd00"   # media amarilla punteada
    OUTLIER_COLOR  = "#b2dfdb"   # outliers en verde claro
    for i, point in enumerate(fae_points):
        serie = point_data.get(point["id"], {}).get(constellation_name, {}).get("serie_lat_ms", [])
        if not serie:
            continue
        figure.add_trace(go.Box(
            y=serie,
            name=f"{point['id']} ({point['nombre']})",
            marker=dict(color=OUTLIER_COLOR, size=5, symbol="circle-open"),
            line=dict(color=BOX_COLOR, width=1.8),
            fillcolor=BOX_FILL,
            median=dict(color=MEDIAN_COLOR, width=2),
            # Línea de media amarilla punteada
            boxmean="sd",
            whiskerwidth=0.5,
        ))
    figure.update_traces(
        meanline=dict(visible=True, color=MEAN_COLOR, width=1.8),
        selector=dict(type="box"),
    )
    figure.update_layout(
        title=dict(
            text="📦 Distribución de latencia por punto FAE",
            font=dict(size=13, color="#ffffff", family="sans-serif"),
            x=0.5, xanchor="center",
        ),
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#cccccc"),
        height=420,
        margin=dict(l=60, r=30, t=60, b=60),
        showlegend=True,
        legend=dict(
            orientation="v", x=1.01, y=1,
            bgcolor="rgba(0,0,0,0)", font=dict(size=10),
            itemsizing="constant",
        ),
        yaxis=dict(
            title=dict(text="Latencia (ms)", font=dict(size=13, color="#ffffff")),
            gridcolor="#2a2a2a", gridwidth=1, griddash="dot",
            zeroline=False,
            tickfont=dict(size=12, color="#ffffff"),
            tickcolor="#ffffff",
            linecolor="#444444", linewidth=1,
        ),
        xaxis=dict(
            gridcolor="#2a2a2a",
            tickfont=dict(size=12, color="#ffffff", family="Courier New, monospace"),
            tickcolor="#ffffff",
            linecolor="#444444", linewidth=1,
        ),
    )
    # Agregar entradas manuales de leyenda para Mediana y Media
    figure.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines",
        line=dict(color=MEDIAN_COLOR, width=2),
        name="Mediana", showlegend=True,
    ))
    figure.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines",
        line=dict(color=MEAN_COLOR, width=2, dash="dash"),
        name="Media", showlegend=True,
    ))
    st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG)
