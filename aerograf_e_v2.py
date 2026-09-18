"""AEROGRAF-E: interfaz Streamlit para el analisis aeroespacial ecuatoriano."""

import datetime
import os

import streamlit as st

from aerograf_src import (
	CIUDADES_ECUADOR,
	CONSTELACIONES,
	PUNTOS_FAE,
	REGIONES,
	build_isl,
	build_networkx,
	compute_all_levels,
	compute_graph_metrics,
	gen_tles,
	graph_metrics,
	load_precomputed,
	propagate,
	propagate_constellation,
)
from aerograf_src.views_grafo import render_tab2
from aerograf_src.views_indices import render_tab3
from aerograf_src.views_observar import render_tab1
from aerograf_src.views_datos_orbitales import render_tab_datos_orbitales
from aerograf_src.views_pasos import render_tab_pasos
from aerograf_src.views_reportes import render_tab_reportes
from activos_reales import cargar_activos, render_tab_datos_reales
import celestrak_api
import keeptrack_api
from keeptrack_api import get_real_tles, get_real_tles_with_status


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
		st.markdown("### 🛰️ Fuente de datos")
		data_source = st.radio(
			"Fuente", ["Sintético (simulación)", "KeepTrack", "CelesTrak"], index=0,
		)
		api_key_input = ""
		if data_source == "KeepTrack":
			api_key_input = st.text_input(
				"API key KeepTrack", type="password",
				help="Gratis en keeptrack.space (menú de usuario > API Key). "
				"Se puede definir también en st.secrets o la variable de entorno KEEPTRACK_API_KEY.",
			)
			if api_key_input:
				st.caption(f"Clave: {'•' * max(0, len(api_key_input) - 4)}{api_key_input[-4:]}")
		refresh_clicked = st.button("🔄 ACTUALIZAR DATOS", use_container_width=True)
		if st.session_state.get("last_update"):
			st.caption(f"Última actualización:  \n{st.session_state['last_update']}")
			st.caption(f"Activos cargados:  \n{st.session_state.get('activos_cargados', 0):,}")
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
	return name, offset, elevation, show_isl, show_coverage, data_source, api_key_input, refresh_clicked


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


def render_comparison(predata, offset, tles_by_constellation=None):
	st.markdown("#### Comparación simultánea de constelaciones")
	columns = st.columns(3)
	for column, (name, config) in zip(columns, CONSTELACIONES.items()):
		with column:
			if tles_by_constellation:
				from aerograf_src.data import satellites_over_ecuador
				now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=offset)
				sats_c = satellites_over_ecuador(propagate(tles_by_constellation[name], now))
				edges_c = build_isl(sats_c)[1] if config["isl"] else []
				metrics = {**graph_metrics(build_networkx(sats_c, edges_c)), "sats_ec": len(sats_c)}
			else:
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


@st.cache_data(ttl=3600, show_spinner=False)
def _compute_real_predata(tles_by_constellation, tle_source):
	"""Recalcula ICA/ICAT/metricas para las 3 constelaciones con TLE reales.

	Cacheado 1h (misma vida util que el catalogo de KeepTrack) porque
	recorrer el catalogo real completo para las 19 muestras temporales
	es costoso; no debe repetirse en cada rerun de Streamlit.
	"""
	return compute_all_levels(
		tles_by_constellation=tles_by_constellation, tle_source=tle_source,
	)


render_header()
name, offset, elevation, show_isl, show_coverage, data_source, api_key_input, refresh_clicked = render_sidebar()
config = {**CONSTELACIONES[name], "name": name}

if refresh_clicked:
	keeptrack_api.fetch_catalog_brief.clear()
	celestrak_api.fetch_group_tle.clear()
	_compute_real_predata.clear()

with st.spinner("Cargando datos orbitales y métricas..."):
	predata = load_precomputed(PROJECT_DIR)
	sats = propagate_constellation(name, time_offset_min=offset)
	edges = build_isl(sats)[1] if config["isl"] else []
	metrics = compute_graph_metrics(name, offset)

# tles_by_constellation siempre queda poblado (real o sintetico) para que
# la pestaña DATOS ORBITALES tenga catalogo que mostrar en cualquier modo.
tles_by_constellation, tle_source, missing, source_errors = {}, {}, [], {}
for cname in CONSTELACIONES:
	real_tles, error_reason = [], None
	if data_source == "KeepTrack":
		real_tles, error_reason = get_real_tles_with_status(cname, api_key_input or None)
	elif data_source == "CelesTrak":
		real_tles, error_reason = celestrak_api.get_real_tles_with_status(cname)
	if real_tles:
		tles_by_constellation[cname] = real_tles
		tle_source[cname] = "real"
	else:
		tles_by_constellation[cname] = gen_tles(CONSTELACIONES[cname])
		tle_source[cname] = "synthetic"
		if data_source != "Sintético (simulación)":
			missing.append(cname)
			if error_reason:
				source_errors[cname] = error_reason

real_tles_notice = None
if data_source != "Sintético (simulación)":
	from aerograf_src.data import satellites_over_ecuador

	if tle_source.get(name) == "real":
		now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=offset)
		with st.spinner(f"Propagando TLEs reales de {name}..."):
			all_sats = propagate(tles_by_constellation[name], now)
			# Constelaciones reales tienen miles de sats: limitar al radio de
			# analisis de Ecuador evita el costo O(n^2) de build_isl sobre todos.
			sats = satellites_over_ecuador(all_sats)
			edges = build_isl(sats)[1] if config["isl"] else []
			metrics = {**graph_metrics(build_networkx(sats, edges)), "sats_ec": len(sats)}

		with st.spinner("Calculando ICA/ICAT e histórico con datos reales (usa cache de 1h)..."):
			real_predata = _compute_real_predata(tles_by_constellation, tle_source)
		if real_predata:
			predata = real_predata

		st.session_state["last_update"] = datetime.datetime.now(datetime.timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
		st.session_state["activos_cargados"] = sum(len(t) for t in tles_by_constellation.values())

		notice = (
			f"Usando TLEs reales de {data_source} para {name}: {len(all_sats)} sats "
			f"en la constelación, {len(sats)} sobre el radio de análisis de Ecuador. "
			"Todas las pestañas (CARACTERIZAR, CONCIENTIZAR, COMPARACIÓN) usan estos datos."
		)
		if missing:
			notice += f" (Sin datos reales para: {', '.join(missing)}; se usa escenario sintético en esas.)"
		real_tles_notice = ("ok", notice)
	else:
		real_tles_notice = (
			"warn",
			source_errors.get(name, f"No se pudieron obtener TLEs reales de {data_source} para {name}."),
		)

kpi = st.columns(6)
kpi[0].metric("Sats totales", len(sats))
kpi[1].metric("Sobre Ecuador", metrics.get("sats_ec", 0))
kpi[2].metric("ISL", metrics.get("aristas", 0))
kpi[3].metric("Grado promedio", metrics.get("grado_promedio", 0))
kpi[4].metric("Clustering", metrics.get("clustering", 0))
kpi[5].metric("Componentes", metrics.get("componentes", 0))

if real_tles_notice:
	status, message = real_tles_notice
	(st.success if status == "ok" else st.warning)(message)
st.divider()

tab_orb, tab1, tab2, tab_pasos, tab3, tab_rep, tab4, tab5, tab0 = st.tabs([
	"🛰️ DATOS ORBITALES",
	"① OBSERVAR", "② CARACTERIZAR", "④ PRÓXIMOS PASOS", "③ CONCIENTIZAR",
	"📄 REPORTES", "🔄 COMPARACIÓN", "📋 METODOLOGÍA",
	"⓪ DATOS REALES",
])

with tab_orb:
	render_tab_datos_orbitales(tles_by_constellation, tle_source,
								st.session_state.get("last_update"), data_source)
with tab1:
	render_tab1(sats, edges, config, REGIONES, PUNTOS_FAE, elevation,
				show_isl, show_coverage, predata, offset)
with tab2:
	render_tab2(sats, config, REGIONES, PUNTOS_FAE, metrics, predata,
				constellations=CONSTELACIONES, ciudades=CIUDADES_ECUADOR)
with tab_pasos:
	render_tab_pasos(tles_by_constellation.get(name, []), CIUDADES_ECUADOR, name, config["color"])
with tab3:
	render_tab3(predata.get("nivel3", {}), name, REGIONES, PUNTOS_FAE,
				CONSTELACIONES)
with tab_rep:
	render_tab_reportes(tles_by_constellation, CIUDADES_ECUADOR + PUNTOS_FAE, list(CONSTELACIONES))
with tab4:
	render_comparison(predata, offset, tles_by_constellation)
with tab5:
	render_methodology()
with tab0:
	render_tab_datos_reales(activos_reales_df)

st.divider()
st.caption("AEROGRAF-E · SGP4 + NetworkX + Plotly · Fuerza Aérea Ecuatoriana · 2026")
