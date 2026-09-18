"""Vista Streamlit: REPORTES — resumen descargable (CSV/PDF) de pasos sobre Ecuador."""

import datetime
import io

import pandas as pd
import streamlit as st

from .passes import calcular_pasos

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

HORIZONTES = {
    "Próximas 6 horas": (360, 1),
    "Próximas 12 horas": (720, 2),
    "Próximas 24 horas": (1440, 4),
}


def _generar_pdf(resumen: dict, pasos: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Reporte AEROGRAF-E")
    styles = getSampleStyleSheet()
    elementos = [
        Paragraph("REPORTE AEROGRAF-E", styles["Title"]),
        Paragraph(
            f"Constelación: {resumen['constelacion']} · Región/punto: {resumen['region']}",
            styles["Normal"],
        ),
        Paragraph(
            f"Periodo: {resumen['periodo']} · Elevación mínima: {resumen['min_el']}° · "
            f"Generado: {datetime.datetime.now(datetime.timezone.utc):%d/%m/%Y %H:%M} UTC",
            styles["Normal"],
        ),
        Spacer(1, 14),
    ]

    resumen_data = [
        ["Activos analizados", str(resumen["activos_analizados"])],
        ["Activos con paso sobre Ecuador", str(resumen["activos_con_paso"])],
        ["Número de pasos", str(resumen["n_pasos"])],
        ["Duración acumulada (min)", str(resumen["duracion_total"])],
        ["Elevación máxima (°)", str(resumen["elevacion_maxima"])],
    ]
    tabla_resumen = Table(resumen_data, colWidths=[260, 150])
    tabla_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elementos += [tabla_resumen, Spacer(1, 18), Paragraph("Tabla de pasos", styles["Heading3"]), Spacer(1, 6)]

    tabla_pasos = [["Satélite", "Punto", "Inicio", "Fin", "Dur. (min)", "Elev. máx (°)"]]
    for paso in pasos[:300]:
        tabla_pasos.append([
            paso["satelite"], paso["punto"], paso["inicio"], paso["fin"],
            str(paso["duracion_min"]), str(paso["elevacion_max"]),
        ])
    tabla = Table(tabla_pasos, colWidths=[95, 85, 50, 50, 65, 75], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00274d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))
    elementos.append(tabla)
    doc.build(elementos)
    return buffer.getvalue()


def render_tab_reportes(tles_by_constellation: dict, puntos: list, constellation_names: list):
    st.markdown("### 📄 REPORTES")
    st.markdown(
        "<div style='background:linear-gradient(90deg,#1a1a00,#00100d);border-left:2px solid #ffcc00;padding:10px 14px;margin:8px 0 18px;color:#fff2b8;font-size:12px'>"
        "Genera un resumen exportable (CSV/PDF) de los pasos satelitales sobre uno o varios puntos de Ecuador.</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        constelacion = st.selectbox("Constelación", constellation_names, key="rep_const")
    with col2:
        region_nombre = st.selectbox("Región/punto", ["Todos"] + [p["nombre"] for p in puntos], key="rep_region")
    with col3:
        min_el = st.slider("Elevación mínima (°)", 5, 60, 20, 5, key="rep_min_el")
    with col4:
        horizonte_label = st.selectbox("Periodo", list(HORIZONTES), key="rep_horizonte")

    if st.button("📊 GENERAR REPORTE", use_container_width=True):
        tles = tles_by_constellation.get(constelacion, [])
        horizonte_min, paso_min = HORIZONTES[horizonte_label]
        t0 = datetime.datetime.now(datetime.timezone.utc)
        puntos_calculo = puntos if region_nombre == "Todos" else [p for p in puntos if p["nombre"] == region_nombre]

        all_pasos = []
        with st.spinner("Calculando pasos para el reporte..."):
            for punto in puntos_calculo:
                for paso in calcular_pasos(tles, punto, t0, horizonte_min, paso_min, min_el):
                    all_pasos.append({**paso, "punto": punto["nombre"]})
        all_pasos.sort(key=lambda p: p["inicio_min"])

        resumen = {
            "constelacion": constelacion, "region": region_nombre,
            "periodo": horizonte_label, "min_el": min_el,
            "activos_analizados": len(tles),
            "activos_con_paso": len({p["satelite"] for p in all_pasos}),
            "n_pasos": len(all_pasos),
            "duracion_total": round(sum(p["duracion_min"] for p in all_pasos), 1),
            "elevacion_maxima": max((p["elevacion_max"] for p in all_pasos), default=0),
        }
        st.session_state["reporte"] = {"resumen": resumen, "pasos": all_pasos}

    reporte = st.session_state.get("reporte")
    if not reporte:
        st.info("Configura los filtros y presiona GENERAR REPORTE.")
        return

    resumen, pasos = reporte["resumen"], reporte["pasos"]
    st.divider()
    st.markdown(f"#### Resumen — {resumen['constelacion']} · {resumen['region']} · {resumen['periodo']}")
    m = st.columns(5)
    m[0].metric("Activos analizados", resumen["activos_analizados"])
    m[1].metric("Activos con paso", resumen["activos_con_paso"])
    m[2].metric("Número de pasos", resumen["n_pasos"])
    m[3].metric("Duración acumulada (min)", resumen["duracion_total"])
    m[4].metric("Elevación máxima (°)", resumen["elevacion_maxima"])

    st.divider()
    st.markdown("#### Tabla de pasos")
    df = pd.DataFrame([{
        "Satélite": p["satelite"], "Punto": p["punto"], "Inicio": p["inicio"],
        "Fin": p["fin"], "Duración (min)": p["duracion_min"], "Elev. máx (°)": p["elevacion_max"],
    } for p in pasos])
    st.dataframe(df, use_container_width=True, height=360)

    st.divider()
    col_csv, col_pdf = st.columns(2)
    col_csv.download_button(
        "⬇️ Descargar CSV", data=df.to_csv(index=False).encode("utf-8"),
        file_name="reporte_aerograf_e.csv", mime="text/csv", use_container_width=True,
    )
    if REPORTLAB_OK:
        col_pdf.download_button(
            "⬇️ Descargar PDF", data=_generar_pdf(resumen, pasos),
            file_name="reporte_aerograf_e.pdf", mime="application/pdf", use_container_width=True,
        )
    else:
        col_pdf.caption("Instala 'reportlab' (pip install reportlab) para exportar PDF.")
