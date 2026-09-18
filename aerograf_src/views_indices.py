"""Vista Streamlit del nivel 3: ICA e ICAT regional."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from .visualization import THEME, THEME_GEO, geo_layout


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
        for name, values in zip(regions, selected):
            point = regions[name]
            figure.add_trace(go.Scattergeo(
                lat=[point["lat"]], lon=[point["lon"]],
                mode="markers+text", text=[f"ICA={values.get('ica', 0):.0f}"],
                textposition="top center",
                marker=dict(size=24, color=values.get("ica", 0),
                            colorscale="RdYlGn", cmin=0, cmax=100),
                name=name,
                hovertemplate=(f"{name}<br>ICA: {values.get('ica', 0):.1f}"
                               f"<br>ICAT: {values.get('icat', 0):.1f}"),
            ))
        for point in fae_points:
            figure.add_trace(go.Scattergeo(
                lat=[point["lat"]], lon=[point["lon"]],
                mode="markers+text", text=[point["id"]],
                marker=dict(size=12, color="#ff3333", symbol="triangle-up"),
                showlegend=False,
            ))
        figure.update_layout(**THEME_GEO, geo=geo_layout(), height=420,
                             margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(figure, use_container_width=True)
    with right:
        st.markdown("#### Radar ICA — todas las constelaciones")
        figure = go.Figure()
        names = list(regions)
        for name, config in constellations.items():
            values = [regional.get(region, {}).get(name, {}).get("ica", 0)
                      for region in names]
            figure.add_trace(go.Scatterpolar(
                r=values + [values[0]], theta=names + [names[0]],
                fill="toself", name=name, line=dict(color=config["color"], width=2),
            ))
        figure.update_layout(
            **{key: value for key, value in THEME.items() if key not in ("xaxis", "yaxis")},
            polar=dict(bgcolor="#0a0a0a", radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1a1a1a")),
            height=420, margin=dict(l=35, r=35, t=25, b=25),
        )
        st.plotly_chart(figure, use_container_width=True)
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
            name=name, x=list(regions), y=values, marker_color=config["color"],
            text=[f"{value:.0f}" for value in values], textposition="outside",
        ))
    figure.add_hline(y=70, line_dash="dash", line_color="#ff3333",
                     annotation_text="Umbral operacional (70)")
    figure.update_layout(**THEME, height=360, barmode="group",
                         yaxis_title="ICA (%)", yaxis_range=[0, 115])
    st.plotly_chart(figure, use_container_width=True)

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
