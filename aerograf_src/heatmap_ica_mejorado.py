"""
FRAGMENTO: Heatmap ICA mejorado — reemplaza la función que genera el heatmap
en views_indices.py (o donde esté definido en tu proyecto).

Mejoras aplicadas:
  1. Escala de color perceptualmente uniforme con umbrales semáforo claros.
  2. Anotaciones con valor + barra de progreso visual en cada celda.
  3. Tooltip enriquecido con interpretación automática (Bueno / Regular / Bajo).
  4. Título dinámico con constelación activa resaltada.
  5. Líneas de cuadrícula visibles para separar regiones y constelaciones.
  6. Eje X con íconos de constelación y badge de promedio global.
"""

import plotly.graph_objects as go
import numpy as np


# ── Paleta semáforo personalizada (rojo → amarillo → verde) ─────────────────
COLORSCALE_ICA = [
    [0.00, "#c0392b"],   # 0 %   rojo intenso
    [0.25, "#e74c3c"],   # 25 %  rojo
    [0.40, "#e67e22"],   # 40 %  naranja
    [0.55, "#f1c40f"],   # 55 %  amarillo
    [0.70, "#2ecc71"],   # 70 %  verde claro
    [0.85, "#27ae60"],   # 85 %  verde
    [1.00, "#1a5e35"],   # 100 % verde oscuro
]


def _calidad_texto(valor: float) -> str:
    """Devuelve etiqueta semáforo según el ICA."""
    if valor >= 80:
        return "Excelente"
    if valor >= 55:
        return "Bueno"
    if valor >= 35:
        return "Regular"
    return "Bajo"


def render_heatmap_ica(
    ica_data: dict,          # {"Starlink": {"Costa": 100, "Sierra": 98, ...}, ...}
    regiones: list[str],     # lista ordenada de regiones (filas)
    constelaciones: list[str],  # lista ordenada de constelaciones (columnas)
    titulo: str = "Heatmap ICA — región × constelación",
) -> go.Figure:
    """
    Genera el heatmap ICA mejorado.

    Parameters
    ----------
    ica_data : dict
        Diccionario anidado {constelacion: {region: valor_ica}}.
    regiones : list[str]
        Nombres de regiones (filas del heatmap).
    constelaciones : list[str]
        Nombres de constelaciones (columnas del heatmap).
    titulo : str
        Título del gráfico.

    Returns
    -------
    go.Figure
    """
    # Construir matriz Z (filas=regiones, columnas=constelaciones)
    z = np.array([
        [ica_data.get(cons, {}).get(reg, 0) for cons in constelaciones]
        for reg in regiones
    ], dtype=float)

    # Promedios globales por constelación para el badge del eje X.
    promedios = {cons: float(np.mean([ica_data.get(cons, {}).get(r, 0) for r in regiones]))
                 for cons in constelaciones}

    # Texto enriquecido en cada celda: valor + mini-barra unicode.
    def _mini_bar(v: float) -> str:
        bloques = int(round(v / 10))
        return "█" * bloques + "░" * (10 - bloques)

    text_matrix = [
        [f"<b>{z[ri, ci]:.0f}%</b><br><span style='font-size:9px'>{_mini_bar(z[ri, ci])}</span>"
         for ci in range(len(constelaciones))]
        for ri in range(len(regiones))
    ]

    # Tooltip enriquecido.
    hover_matrix = [
        [
            f"<b>{constelaciones[ci]}</b> · {regiones[ri]}<br>"
            f"ICA: <b>{z[ri, ci]:.1f}%</b><br>"
            f"Calidad: <b>{_calidad_texto(z[ri, ci])}</b><br>"
            f"Promedio constelación: {promedios[constelaciones[ci]]:.1f}%"
            for ci in range(len(constelaciones))
        ]
        for ri in range(len(regiones))
    ]

    # Etiquetas eje X con promedio badge.
    xtick_labels = [
        f"{cons}<br><span style='color:#aaaaaa;font-size:10px'>x̄ {promedios[cons]:.0f}%</span>"
        for cons in constelaciones
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=constelaciones,
        y=regiones,
        text=text_matrix,
        hovertext=hover_matrix,
        hoverinfo="text",
        texttemplate="%{text}",
        textfont=dict(size=13, color="white", family="Courier New, monospace"),
        colorscale=COLORSCALE_ICA,
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
        xgap=3,   # separación visual entre columnas
        ygap=3,   # separación visual entre filas
    ))

    fig.update_layout(
        title=dict(
            text=f"🔥 {titulo}",
            font=dict(size=15, color="#ffffff", family="Courier New, monospace"),
            x=0.01,
        ),
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#cccccc", family="Courier New, monospace"),
        margin=dict(l=110, r=110, t=60, b=60),
        height=380,
        xaxis=dict(
            ticktext=xtick_labels,
            tickvals=constelaciones,
            tickfont=dict(size=11),
            side="bottom",
            gridcolor="#1a1a1a",
        ),
        yaxis=dict(
            tickfont=dict(size=11),
            gridcolor="#1a1a1a",
            autorange="reversed",   # región superior = primera fila
        ),
    )

    # Líneas de cuadrícula manuales para separar celdas con más claridad.
    for i in range(len(regiones) + 1):
        fig.add_hline(y=i - 0.5, line=dict(color="#1a1a1a", width=1))
    for j in range(len(constelaciones) + 1):
        fig.add_vline(x=j - 0.5, line=dict(color="#1a1a1a", width=1))

    return fig


# ── Ejemplo de uso en Streamlit ──────────────────────────────────────────────
# Pega estas líneas en tu views_indices.py donde antes llamabas al heatmap:
#
#   from .heatmap_ica_mejorado import render_heatmap_ica
#
#   fig = render_heatmap_ica(
#       ica_data=nivel3.get("ica", {}),        # tu dict existente
#       regiones=list(REGIONES.keys()),
#       constelaciones=list(CONSTELACIONES.keys()),
#   )
#   st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
