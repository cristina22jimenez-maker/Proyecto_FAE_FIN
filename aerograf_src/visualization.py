"""
visualization.py — Layouts y helpers de Plotly para AEROGRAF-E
══════════════════════════════════════════════════════════════
Centraliza todos los temas visuales, colores y configuraciones
de Plotly para garantizar consistencia en toda la aplicación.

No importa nada de orbital/visibility/graph — solo Plotly.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# PALETA DE COLORES — ESTILO OSIRIS
# ═══════════════════════════════════════════════════════════════════════════════
# Constelaciones
COLOR_STARLINK = "#00aaff"    # Azul neón
COLOR_ONEWEB   = "#00ff88"    # Verde neón
COLOR_KUIPER   = "#ffcc00"    # Amarillo neón

# Regiones Ecuador
COLOR_COSTA      = "#00aaff"
COLOR_SIERRA     = "#00ff88"
COLOR_AMAZONIA   = "#ffcc00"
COLOR_GALAPAGOS  = "#ff44aa"
COLOR_FRONTERA_N = "#ff6600"
COLOR_FRONTERA_S = "#cc44ff"

# Puntos FAE
COLOR_P1 = "#ff3333"   # base
COLOR_P2 = "#00aaff"   # investigacion
COLOR_P3 = "#00ff88"   # gateway
COLOR_P4 = "#ffcc00"   # antena

PT_COLORS  = [COLOR_P1, COLOR_P2, COLOR_P3, COLOR_P4]
PT_SYMBOLS = {
    "base":         "triangle-up",
    "investigacion":"square",
    "gateway":      "diamond",
    "antena":       "star",
}

# UI general
COLOR_ACCENT  = "#00ff88"
COLOR_TEXT    = "#ffffff"
COLOR_MUTED   = "#888888"
COLOR_BG      = "#000000"
COLOR_SURFACE = "#0c0c0c"
COLOR_BORDER  = "#1e1e1e"


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def hex_rgba(hex_color: str, alpha: float = 0.15) -> str:
    """
    Convierte un color hex (#rrggbb) a formato rgba() de CSS/Plotly.
    Plotly no acepta colores hex de 8 dígitos (#rrggbbaa).
    """
    h    = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ═══════════════════════════════════════════════════════════════════════════════
# TEMAS PLOTLY — ESTILO OSIRIS
# ═══════════════════════════════════════════════════════════════════════════════
THEME = dict(
    paper_bgcolor=COLOR_BG,
    plot_bgcolor="#080808",
    font=dict(color=COLOR_TEXT, family="Courier New, monospace"),
    xaxis=dict(
        gridcolor="#1a1a1a",
        zerolinecolor="#222222",
        tickfont=dict(color=COLOR_MUTED),
        title=dict(font=dict(color="#aaaaaa")),
    ),
    yaxis=dict(
        gridcolor="#1a1a1a",
        zerolinecolor="#222222",
        tickfont=dict(color=COLOR_MUTED),
        title=dict(font=dict(color="#aaaaaa")),
    ),
)

THEME_GEO = dict(
    paper_bgcolor=COLOR_BG,
    plot_bgcolor="#080808",
    font=dict(color=COLOR_TEXT, family="Courier New, monospace"),
)

LEGEND_STYLE = dict(
    bgcolor=COLOR_SURFACE,
    bordercolor=COLOR_BORDER,
    borderwidth=1,
    font=dict(size=10, color=COLOR_TEXT),
)


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT GEOGRÁFICO — MAPA ESTILO OSIRIS
# ═══════════════════════════════════════════════════════════════════════════════
def geo_layout(lon_range: list = None,
               lat_range: list = None) -> dict:
    """
    Configuración del objeto 'geo' de Plotly para el mapa ecuatoriano.
    Tierra gris carbón, océano negro, fronteras blancas sutiles.

    Parámetros:
        lon_range : [min_lon, max_lon] — por defecto Ecuador ampliado
        lat_range : [min_lat, max_lat] — por defecto Ecuador ampliado
    """
    return dict(
        scope="world",
        showland=True,       landcolor="#2a2a2a",
        showocean=True,      oceancolor="#000000",
        showlakes=True,      lakecolor="#000000",
        showrivers=False,
        showcountries=True,  countrycolor="#888888",  countrywidth=1.2,
        showcoastlines=True, coastlinecolor="#aaaaaa", coastlinewidth=1.5,
        showsubunits=True,   subunitcolor="#666666",  subunitwidth=0.8,
        showframe=True,      framecolor="#555555",
        lonaxis=dict(
            range=lon_range or [-95, -73],
            showgrid=True, gridcolor="#222222", gridwidth=0.5, dtick=5,
        ),
        lataxis=dict(
            range=lat_range or [-7, 3],
            showgrid=True, gridcolor="#222222", gridwidth=0.5, dtick=2,
        ),
        bgcolor="#000000",
        projection_type="mercator",
        resolution=50,
    )
