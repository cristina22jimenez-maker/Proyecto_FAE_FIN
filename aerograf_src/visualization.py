"""
visualization.py — Layouts y helpers de Plotly para AEROGRAF-E
══════════════════════════════════════════════════════════════
Centraliza temas, paletas y trazas reutilizables para que todos
los gráficos compartan el mismo lenguaje visual (tema oscuro).
"""

import plotly.graph_objects as go

# ═══════════════════════════════════════════════════════════════════════════════
# PALETA — ESTILO OSIRIS
# ═══════════════════════════════════════════════════════════════════════════════
COLOR_STARLINK = "#00aaff"
COLOR_ONEWEB   = "#00ff88"
COLOR_KUIPER   = "#ffcc00"

COLOR_COSTA      = "#00aaff"
COLOR_SIERRA     = "#00ff88"
COLOR_AMAZONIA   = "#ffcc00"
COLOR_GALAPAGOS  = "#ff44aa"
COLOR_FRONTERA_N = "#ff6600"
COLOR_FRONTERA_S = "#cc44ff"

COLOR_P1 = "#ff3333"
COLOR_P2 = "#00aaff"
COLOR_P3 = "#00ff88"
COLOR_P4 = "#ffcc00"

PT_COLORS  = [COLOR_P1, COLOR_P2, COLOR_P3, COLOR_P4]
PT_SYMBOLS = {
    "base":          "triangle-up",
    "investigacion": "square",
    "gateway":       "diamond",
    "antena":        "star",
}

COLOR_ACCENT  = "#00ff88"
COLOR_TEXT    = "#ffffff"
COLOR_MUTED   = "#888888"
COLOR_BG      = "#000000"
COLOR_SURFACE = "#0c0c0c"
COLOR_BORDER  = "#1e1e1e"
COLOR_PLOT    = "#080808"

# Escala ICA sobre fondo negro: rojo → ámbar → verde neón
ICA_COLORSCALE = [
    [0.00, "#3a0a0a"],
    [0.35, "#cc3333"],
    [0.70, "#ffcc00"],
    [1.00, "#00ff88"],
]

FONT_FAMILY = "Courier New, monospace"

CHART_CONFIG = dict(
    displaylogo=False,
    scrollZoom=False,
    modeBarButtonsToRemove=["lasso2d", "select2d", "autoScale2d"],
    toImageButtonOptions=dict(
        format="png", filename="aerograf-e", scale=2,
        height=720, width=1280,
    ),
)

HOVERLABEL = dict(
    bgcolor="rgba(12,12,12,0.92)",
    bordercolor="#2a2a2a",
    font=dict(color=COLOR_TEXT, family=FONT_FAMILY, size=11),
)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def hex_rgba(hex_color: str, alpha: float = 0.15) -> str:
    """Convierte un color hex (#rrggbb) a rgba() de Plotly."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def colorbar(title: str, x: float = 1.02) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=10, color=COLOR_MUTED, family=FONT_FAMILY)),
        tickfont=dict(size=9, color=COLOR_MUTED, family=FONT_FAMILY),
        bgcolor="rgba(0,0,0,0)",
        outlinecolor=COLOR_BORDER,
        outlinewidth=0,
        thickness=12,
        len=0.72,
        x=x,
        y=0.5,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEMAS
# ═══════════════════════════════════════════════════════════════════════════════
THEME = dict(
    paper_bgcolor=COLOR_BG,
    plot_bgcolor=COLOR_PLOT,
    font=dict(color=COLOR_TEXT, family=FONT_FAMILY, size=11),
    hoverlabel=HOVERLABEL,
    hovermode="closest",
    xaxis=dict(
        gridcolor="#1a1a1a",
        zeroline=False,
        tickfont=dict(color=COLOR_MUTED, size=10),
        title=dict(font=dict(color="#aaaaaa", size=11)),
        showline=True, linecolor="#222222", linewidth=1,
        showspikes=True, spikecolor="#333333", spikethickness=1,
        spikedash="dot", spikemode="across",
    ),
    yaxis=dict(
        gridcolor="#1a1a1a",
        zeroline=False,
        tickfont=dict(color=COLOR_MUTED, size=10),
        title=dict(font=dict(color="#aaaaaa", size=11)),
        showline=True, linecolor="#222222", linewidth=1,
        showspikes=True, spikecolor="#333333", spikethickness=1,
        spikedash="dot", spikemode="across",
    ),
)

THEME_GEO = dict(
    paper_bgcolor=COLOR_BG,
    plot_bgcolor=COLOR_PLOT,
    font=dict(color=COLOR_TEXT, family=FONT_FAMILY),
    hoverlabel=HOVERLABEL,
    dragmode="pan",
)

LEGEND_STYLE = dict(
    bgcolor="rgba(12,12,12,0.85)",
    bordercolor=COLOR_BORDER,
    borderwidth=1,
    font=dict(size=10, color=COLOR_TEXT, family=FONT_FAMILY),
    itemsizing="constant",
)


def legend_h(y: float = 1.08) -> dict:
    return dict(
        **LEGEND_STYLE,
        orientation="h",
        yanchor="bottom", y=y,
        xanchor="left", x=0,
    )


def apply_xy_theme(figure: go.Figure, height: int = 360, **layout_kw) -> go.Figure:
    """Aplica el tema cartesiano y márgenes compactos."""
    layout = dict(
        **THEME,
        height=height,
        margin=dict(l=48, r=24, t=40, b=44),
        legend=legend_h(),
    )
    layout.update(layout_kw)
    figure.update_layout(**layout)
    return figure


def apply_geo_theme(figure: go.Figure, height: int = 440, **layout_kw) -> go.Figure:
    layout = dict(
        **THEME_GEO,
        geo=geo_layout(),
        height=height,
        margin=dict(l=0, r=0, t=8, b=0),
        legend=legend_h(y=1.02),
    )
    layout.update(layout_kw)
    figure.update_layout(**layout)
    return figure


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT GEOGRÁFICO
# ═══════════════════════════════════════════════════════════════════════════════
def geo_layout(lon_range: list = None,
               lat_range: list = None) -> dict:
    """Mapa de Ecuador: océano negro, tierra carbón, grilla sutil."""
    return dict(
        scope="world",
        showland=True,       landcolor="#1c1c1c",
        showocean=True,      oceancolor="#050505",
        showlakes=True,      lakecolor="#050505",
        showrivers=False,
        showcountries=True,  countrycolor="#666666",  countrywidth=1.1,
        showcoastlines=True, coastlinecolor="#9a9a9a", coastlinewidth=1.3,
        showsubunits=True,   subunitcolor="#555555",  subunitwidth=0.7,
        showframe=True,      framecolor="#333333",
        lonaxis=dict(
            range=lon_range or [-95, -73],
            showgrid=True, gridcolor="#1a1a1a", gridwidth=0.4, dtick=5,
        ),
        lataxis=dict(
            range=lat_range or [-7, 3],
            showgrid=True, gridcolor="#1a1a1a", gridwidth=0.4, dtick=2,
        ),
        bgcolor=COLOR_BG,
        projection_type="mercator",
        resolution=50,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TRAZAS GEO REUTILIZABLES
# ═══════════════════════════════════════════════════════════════════════════════
def scattergeo_isl(edges: list, color: str, name: str = "ISL",
                   opacity: float = 0.28, width: float = 0.7,
                   max_edges: int = 400) -> go.Scattergeo:
    """Una sola traza con todas las aristas ISL (evita cientos de traces)."""
    lats, lons = [], []
    for edge in edges[:max_edges]:
        lats.extend([edge.get("lat_a", edge.get("la")),
                     edge.get("lat_b", edge.get("lb")), None])
        lons.extend([edge.get("lon_a", edge.get("loa")),
                     edge.get("lon_b", edge.get("lob")), None])
    return go.Scattergeo(
        lat=lats, lon=lons, mode="lines",
        line=dict(width=width, color=color),
        opacity=opacity, name=name,
        hoverinfo="skip", showlegend=bool(lats),
    )


def scattergeo_sats(sats: list, color: str, name: str = "Satélites",
                    size: float = 6, opacity: float = 0.75) -> go.Scattergeo:
    names = [sat.get("name", "SAT") for sat in sats]
    return go.Scattergeo(
        lat=[sat["lat"] for sat in sats],
        lon=[sat["lon"] for sat in sats],
        mode="markers",
        marker=dict(
            size=size, color=color, opacity=opacity,
            line=dict(width=0.4, color="rgba(255,255,255,0.35)"),
        ),
        name=name,
        text=names,
        customdata=[[sat.get("alt_km", 0), sat.get("inc", 0)] for sat in sats],
        hovertemplate=("<b>%{text}</b><br>"
                       "Lat %{lat:.2f}° · Lon %{lon:.2f}°<br>"
                       "Alt %{customdata[0]:.0f} km · Inc %{customdata[1]:.1f}°"
                       "<extra></extra>"),
    )


def scattergeo_regions(regions: dict, counts: dict = None) -> list:
    traces = []
    counts = counts or {}
    for name, region in regions.items():
        n = counts.get(name)
        label = f"{name}" if n is None else f"{name}  {n}"
        traces.append(go.Scattergeo(
            lat=[region["lat"]], lon=[region["lon"]],
            mode="markers+text",
            text=[label],
            textposition="top center",
            textfont=dict(size=10, color=region["color"], family=FONT_FAMILY),
            marker=dict(
                size=16 if n is None else min(28, 10 + (n or 0)),
                color=hex_rgba(region["color"], 0.35),
                line=dict(width=1.6, color=region["color"]),
                symbol="circle",
            ),
            name=name,
            hovertemplate=(f"<b>{name}</b><br>{region.get('desc', '')}"
                           + (f"<br>Visibles: {n}" if n is not None else "")
                           + "<extra></extra>"),
        ))
    return traces


def scattergeo_fae(points: list, showlegend: bool = True) -> list:
    traces = []
    for i, point in enumerate(points):
        color = PT_COLORS[i % len(PT_COLORS)]
        traces.append(go.Scattergeo(
            lat=[point["lat"]], lon=[point["lon"]],
            mode="markers+text",
            text=[point.get("id", "")],
            textposition="bottom right",
            textfont=dict(size=10, color=color, family=FONT_FAMILY),
            marker=dict(
                size=13, color=color, symbol="triangle-up",
                line=dict(width=0.8, color="#ffffff"),
            ),
            name=point.get("nombre", point.get("id", "FAE")),
            showlegend=showlegend,
            hovertemplate=(f"<b>{point.get('nombre', '')}</b><br>"
                           f"{point.get('id', '')} · {point.get('region', '')}"
                           "<extra></extra>"),
        ))
    return traces
