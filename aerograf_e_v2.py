"""AEROGRAF-E: interfaz Streamlit para el analisis aeroespacial ecuatoriano."""

import datetime
import os

import streamlit as st

from aerograf_src import (
	CONSTELACIONES,
	PUNTOS_FAE,
	REGIONES,
	build_isl,
	compute_graph_metrics,
	load_precomputed,
	propagate_constellation,
)
from aerograf_src.views_grafo import render_tab2
from aerograf_src.views_indices import render_tab3
from aerograf_src.views_observar import render_tab1
from activos_reales import cargar_activos, render_tab_datos_reales
from keeptrack_api import get_real_tles


st.set_page_config(
	page_title="AEROGRAF-E | FAE",
	page_icon="🛰️",
	layout="wide",
	initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background:#000000 !important; color:#ffffff !important; }
[data-testid="stSidebar"] { background:#070707 !important; border-right:1px solid #1e1e1e !important; }
[data-testid="stMetric"] { background:#0c0c0c !important; border:1px solid #1e1e1e !important; border-radius:3px !important; padding:12px !important; text-align:center !important; }
[data-testid="stMetricValue"] { color:#00ff88 !important; font-size:24px !important; font-family:"Courier New",monospace !important; font-weight:700 !important; }
[data-testid="stMetricLabel"] { color:#666666 !important; font-size:9px !important; text-transform:uppercase !important; letter-spacing:2px !important; }
[data-testid="stMetricDelta"] { color:#ffcc00 !important; }
.stTabs [data-baseweb="tab"] { color:#555555 !important; font-size:11px !important; font-weight:700 !important; letter-spacing:2px !important; text-transform:uppercase !important; }
.stTabs [aria-selected="true"] { color:#00ff88 !important; border-bottom-color:#00ff88 !important; }
h1,h2 { color:#ffffff !important; letter-spacing:3px !important; }
h3 { color:#00ff88 !important; letter-spacing:2px !important; }
h4,h5 { color:#cccccc !important; }
[data-testid="stSelectbox"] > div > div { background:#0c0c0c !important; border:1px solid #2a2a2a !important; color:#ffffff !important; border-radius:3px !important; }
[data-testid="stSelectbox"] label, [data-testid="stSlider"] label, [data-testid="stCheckbox"] label { color:#666666 !important; font-size:10px !important; text-transform:uppercase !important; letter-spacing:1px !important; }
.streamlit-expanderHeader { color:#00ff88 !important; font-size:11px !important; font-weight:700 !important; letter-spacing:1px !important; text-transform:uppercase !important; }
.streamlit-expanderContent { background:#0c0c0c !important; border:1px solid #1e1e1e !important; }
p, .stMarkdown p { color:#cccccc !important; }
hr { border-color:#1a1a1a !important; }
code { background:#111111 !important; color:#00ff88 !important; padding:2px 6px !important; border-radius:2px !important; }
.stDataFrame { border:1px solid #1e1e1e !important; border-radius:3px !important; }
::-webkit-scrollbar { width:3px; height:3px; }
::-webkit-scrollbar-track { background:#000000; }
::-webkit-scrollbar-thumb { background:#2a2a2a; border-radius:2px; }
</style>
""", unsafe_allow_html=True)


def render_sidebar():
	with st.sidebar:
		st.markdown("""
		<div style='text-align:center;padding:10px 0'>
		  <div style='font-size:32px'>🛰️</div>
		  <div style='font-size:20px;font-weight:700;color:#4fc3f7;letter-spacing:2px'>AEROGRAF-E</div>
		  <div style='font-size:11px;color:#aaaaaa'>Entorno Aeroespacial Ecuatoriano<br>Grafos Dinámicos LEO · FAE</div>
		</div>
		""", unsafe_allow_html=True)
		st.divider()
		st.markdown("### Parámetros")
		name = st.selectbox("Constelación", list(CONSTELACIONES))
		offset = st.slider("Tiempo orbital (min)", 0, 95, 0, 5)
		elevation = st.slider("Elevación mínima (°)", 5, 45, 25, 5)
		show_isl = st.checkbox("Mostrar ISL", True)
		show_coverage = st.checkbox("Mostrar cobertura", True)
		st.divider()
		use_real_tles = st.checkbox("Usar TLEs reales (KeepTrack API)", False)
		api_key_input = ""
		if use_real_tles:
			api_key_input = st.text_input(
				"API key KeepTrack", type="password",
				help="Gratis en keeptrack.space (menú de usuario > API Key). "
				"Se puede definir también en st.secrets o la variable de entorno KEEPTRACK_API_KEY.",
			)
		st.divider()
		with st.expander("ICA e ICAT"):
			st.markdown("ICA mide cobertura promedio. ICAT pondera ICA por latencia.")
		with st.expander("Grafo temporal"):
			st.markdown("G(T) representa la topología satelital en cada instante.")
		st.divider()
		st.info(
			"AEROGRAF-E integra un registro histórico de activos espaciales "
			"y escenarios de constelaciones LEO. "
			"Los datos del registro no representan seguimiento en tiempo real."
		)
	return name, offset, elevation, show_isl, show_coverage, use_real_tles, api_key_input


def render_header():
	now = datetime.datetime.now(datetime.timezone.utc)
	st.markdown(f"""
	<div style='background:linear-gradient(135deg,#000,#0d0d0d,#000);padding:20px 28px;border-radius:12px;border:1px solid #2a2a2a;margin-bottom:20px'>
	  <div style='font-size:26px;font-weight:700;color:#4fc3f7;letter-spacing:2px'>🛰️ AEROGRAF-E</div>
	  <div style='font-size:13px;color:#aaaaaa'>Caracterización del Entorno Aeroespacial Ecuatoriano mediante Grafos Dinámicos de Constelaciones LEO</div>
	  <div style='font-size:11px;color:#2a4a6a;margin-top:8px'>UTC: {now:%H:%M:%S} · SGP4 · NetworkX · Hypatia · FAE</div>
	  <div style='display:flex;gap:10px;margin-top:14px;flex-wrap:wrap'>
	    <span style='border:1px solid #00aaff;color:#00aaff;border-radius:12px;padding:4px 12px;font-size:10px'>① OBSERVAR</span>
	    <span style='border:1px solid #00ff88;color:#00ff88;border-radius:12px;padding:4px 12px;font-size:10px'>② CARACTERIZAR</span>
	    <span style='border:1px solid #ffcc00;color:#ffcc00;border-radius:12px;padding:4px 12px;font-size:10px'>③ CONCIENTIZAR</span>
	  </div>
	</div>
	""", unsafe_allow_html=True)


def render_comparison(predata, offset):
	st.markdown("#### Comparación simultánea de constelaciones")
	columns = st.columns(3)
	for column, (name, config) in zip(columns, CONSTELACIONES.items()):
		with column:
			metrics = compute_graph_metrics(name, offset)
			st.markdown(f"**{name}**  \n{config['inc']}° · {config['alt_km']} km")
			st.metric("Sats sobre Ecuador", metrics.get("sats_ec", 0))
			st.metric("ISL modelados", metrics.get("aristas", 0))
			st.metric("Clustering", metrics.get("clustering", 0))
	if predata:
		st.markdown("#### Evolución de satélites visibles")
		series = predata.get("nivel1", {}).get("visibilidad", {})
		for name in CONSTELACIONES:
			st.line_chart(series.get(name, {}).get("TOTAL", []), height=180)


def render_methodology():
	st.markdown("#### 📋 Marco metodológico de AEROGRAF-E")
	left, right = st.columns(2)
	with left:
		st.markdown("""
		**Basado en Hypatia (Bhattacherjee et al., IMC 2020)**

		Hypatia demuestra que es posible generar:
		- El estado de los satélites en función del tiempo
		- La conectividad GS-satélite
		- Los ISL y el grafo de red temporal

		AEROGRAF-E adapta este framework para Ecuador con:

		| Hypatia original | AEROGRAF-E |
		|---|---|
		| Ciudades mundiales | Puntos FAE Ecuador |
		| Ground Stations globales | Regiones ecuatorianas |
		| RTT como métrica | ICA/ICAT como índice soberano |
		| Red LEO general | Entorno aeroespacial ecuatoriano |
		| Routing (congestion) | Conectividad y visibilidad |
		| Trayectorias | ✓ Protagonista |
		| ISL | ✓ Protagonista |
		| Grafos dinámicos | ✓ Protagonista |
		| Conciencia situacional | **Nuevo enfoque** |
		| Mapa Ecuador | **Nuevo** |
		| Índice ICA/ICAT | **Aporte propio** |
		""")
	with right:
		st.markdown("""
		**Pipeline técnico:**

		```
		1. ENTRADA
		   ├── TLEs sintéticos (parámetros FCC reales)
		   ├── Puntos FAE (coordenadas reales)
		   └── Regiones Ecuador (6 zonas)

		2. PROPAGACIÓN
		   └── SGP4 (sgp4 library)
		       ├── Posición ECEF en tiempo t
		       └── Latitud, longitud, altitud

		3. GRAFO TEMPORAL G(T)
		   ├── Nodos = satélites sobre Ecuador
		   ├── Aristas ISL (dist < 1800 km)
		   └── Peso = distancia / c (ms)

		4. MÉTRICAS (NetworkX)
		   ├── Densidad, clustering
		   ├── Componente gigante
		   └── Latencia promedio (Dijkstra)

		5. ÍNDICES
		   ├── ICA = visibilidad / umbral × 100
		   └── ICAT = ICA × (1 - latencia/20)

		6. VISUALIZACIÓN (Plotly + Streamlit)
		   ├── Mapa orbital en vivo
		   ├── Grafo ISL proyectado
		   ├── Series temporales
		   └── Radar/heatmap ICA
		```
		""")
	st.divider()
	st.markdown("""
	**Referencia principal:**
	> Bhattacherjee, D., et al. "Exploring the Internet from Space with Hypatia."
	> *ACM IMC 2020*. DOI: 10.1145/3419394.3423635

	**Ventaja clave del enfoque:**
	No se requieren sensores físicos para el prototipo. Las ubicaciones de estaciones
	terrestres son entradas del modelo, tal como lo plantea el artículo de Hypatia.
	El primer prototipo puede ejecutarse completamente en software con TLEs públicos.
	""")


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVOS_CSV = os.path.join(PROJECT_DIR, "activos_espaciales.csv")
activos_reales_df = cargar_activos(ACTIVOS_CSV)

render_header()
name, offset, elevation, show_isl, show_coverage, use_real_tles, api_key_input = render_sidebar()
config = {**CONSTELACIONES[name], "name": name}

with st.spinner("Cargando datos orbitales y métricas..."):
	predata = load_precomputed(PROJECT_DIR)
	sats = propagate_constellation(name, time_offset_min=offset)
	edges = build_isl(sats)[1] if config["isl"] else []
	metrics = compute_graph_metrics(name, offset)

real_tles_notice = None
if use_real_tles:
	from aerograf_src.orbital import propagate as _propagate
	real_tles = get_real_tles(name, api_key_input or None)
	if real_tles:
		now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=offset)
		sats = _propagate(real_tles, now)
		edges = build_isl(sats)[1] if config["isl"] else []
		real_tles_notice = f"Usando {len(sats)} TLEs reales de KeepTrack para {name}."
	else:
		real_tles_notice = "No se pudieron obtener TLEs reales (revisa la API key). Mostrando datos sintéticos."

kpi = st.columns(6)
kpi[0].metric("Sats totales", len(sats))
kpi[1].metric("Sobre Ecuador", metrics.get("sats_ec", 0))
kpi[2].metric("ISL", metrics.get("aristas", 0))
kpi[3].metric("Grado promedio", metrics.get("grado_promedio", 0))
kpi[4].metric("Clustering", metrics.get("clustering", 0))
kpi[5].metric("Componentes", metrics.get("componentes", 0))
st.divider()

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
	"⓪ DATOS REALES",
	"① OBSERVAR", "② CARACTERIZAR", "③ CONCIENTIZAR",
	"🔄 COMPARACIÓN", "📋 METODOLOGÍA",
])

with tab0:
	render_tab_datos_reales(activos_reales_df)
with tab1:
	if real_tles_notice:
		(st.success if use_real_tles and "reales" in real_tles_notice.split(".")[0] else st.warning)(real_tles_notice)
	render_tab1(sats, edges, config, REGIONES, PUNTOS_FAE, elevation,
				show_isl, show_coverage, predata, offset)
with tab2:
	render_tab2(sats, config, REGIONES, PUNTOS_FAE, metrics, predata,
				constellations=CONSTELACIONES)
with tab3:
	render_tab3(predata.get("nivel3", {}), name, REGIONES, PUNTOS_FAE,
				CONSTELACIONES)
with tab4:
	render_comparison(predata, offset)
with tab5:
	render_methodology()

st.divider()
st.caption("AEROGRAF-E · SGP4 + NetworkX + Plotly · Fuerza Aérea Ecuatoriana · 2026")
