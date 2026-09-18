"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  AEROGRAF-E                                                                  ║
║  Caracterización del Entorno Aeroespacial Ecuatoriano                        ║
║  mediante Grafos Dinámicos de Constelaciones LEO                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Tres niveles de análisis:                                                   ║
║   NIVEL 1 — OBSERVAR    ¿Qué satélites pasan sobre Ecuador?                 ║
║   NIVEL 2 — CARACTERIZAR ¿Cómo cambia la estructura del grafo?              ║
║   NIVEL 3 — CONCIENTIZAR ¿Qué tan complejo es el entorno por región?        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Instalación:                                                                ║
║      pip install streamlit plotly sgp4 numpy pandas networkx                ║
║  Ejecución:                                                                  ║
║      streamlit run aerograf_e.py                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import math, heapq, datetime, json, os, sys, urllib.request
import networkx as nx

try:
    from sgp4.api import Satrec, jday
    SGP4_OK = True
except ImportError:
    SGP4_OK = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AEROGRAF-E | FAE",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""<style>
/* ══ AEROGRAF-E — TEMA OSIRIS ══════════════════════════════════════════════ */
.stApp { background:#000000 !important; color:#ffffff !important; }
[data-testid="stSidebar"] {
  background:#070707 !important; border-right:1px solid #1e1e1e !important;
}
[data-testid="stMetric"] {
  background:#0c0c0c !important; border:1px solid #1e1e1e !important;
  border-radius:3px !important; padding:12px !important; text-align:center !important;
}
[data-testid="stMetricValue"] { color:#00ff88 !important; font-size:24px !important;
  font-family:"Courier New",monospace !important; font-weight:700 !important; }
[data-testid="stMetricLabel"] { color:#666666 !important; font-size:9px !important;
  text-transform:uppercase !important; letter-spacing:2px !important; }
[data-testid="stMetricDelta"] { color:#ffcc00 !important; }
.stTabs [data-baseweb="tab"] { color:#555555 !important; font-size:11px !important;
  font-weight:700 !important; letter-spacing:2px !important; text-transform:uppercase !important; }
.stTabs [aria-selected="true"] { color:#00ff88 !important; border-bottom-color:#00ff88 !important; }
h1,h2 { color:#ffffff !important; letter-spacing:3px !important; }
h3    { color:#00ff88 !important; letter-spacing:2px !important; }
h4,h5 { color:#cccccc !important; }
.stSelectbox>div>div { background:#0c0c0c !important; border:1px solid #2a2a2a !important;
  color:#ffffff !important; border-radius:3px !important; }
[data-testid="stSelectbox"] label, [data-testid="stSlider"] label, .stCheckbox label {
  color:#666666 !important; font-size:10px !important;
  text-transform:uppercase !important; letter-spacing:1px !important; }
.streamlit-expanderHeader { color:#00ff88 !important; font-size:11px !important;
  font-weight:700 !important; letter-spacing:1px !important; text-transform:uppercase !important; }
.streamlit-expanderContent { background:#0c0c0c !important; border:1px solid #1e1e1e !important; }
hr { border-color:#1a1a1a !important; }
code { background:#111111 !important; color:#00ff88 !important;
       padding:2px 6px !important; border-radius:2px !important; }
pre  { background:#0c0c0c !important; border:1px solid #1e1e1e !important; border-radius:3px !important; }
.stDataFrame { border:1px solid #1e1e1e !important; border-radius:3px !important; }
p, .stMarkdown p { color:#cccccc !important; }
::-webkit-scrollbar { width:3px; height:3px; }
::-webkit-scrollbar-track { background:#000000; }
::-webkit-scrollbar-thumb { background:#2a2a2a; border-radius:2px; }
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES FÍSICAS
# ═══════════════════════════════════════════════════════════════════════════════
RE_KM   = 6_371.0
GM_KM3  = 398_600.4418
C_KM_S  = 299_792.458
ISL_MAX = 1_800.0
ISL_K   = 4

# ═══════════════════════════════════════════════════════════════════════════════
# DATOS GEOGRÁFICOS Y DE REFERENCIA
# ═══════════════════════════════════════════════════════════════════════════════
REGIONES = {
    "Costa":      {"lat":-1.5,  "lon":-80.0, "color":"#00aaff","desc":"Costa Pacífica"},
    "Sierra":     {"lat":-1.8,  "lon":-78.6, "color":"#00ff88","desc":"Cordillera Andina"},
    "Amazonía":   {"lat":-1.5,  "lon":-76.5, "color":"#ffcc00","desc":"Región Amazónica"},
    "Galápagos":  {"lat":-0.95, "lon":-90.97,"color":"#ff44aa","desc":"Archipiélago"},
    "Frontera N": {"lat": 0.3,  "lon":-77.5, "color":"#ff6600","desc":"Frontera Norte"},
    "Frontera S": {"lat":-4.5,  "lon":-79.0, "color":"#cc44ff","desc":"Frontera Sur"},
}

PUNTOS_FAE = [
    {"id":"P1","nombre":"Checa/Yaruquí", "lat":-0.1454,"lon":-78.3105,"alt_m":2550,"region":"Sierra"},
    {"id":"P2","nombre":"CIDFAE",        "lat":-1.2138,"lon":-78.5764,"alt_m":2850,"region":"Sierra"},
    {"id":"P3","nombre":"El Arenal/GYE", "lat":-2.1620,"lon":-79.8784,"alt_m":10,  "region":"Costa"},
    {"id":"P4","nombre":"Antenas FAE",   "lat":-0.1460,"lon":-78.3107,"alt_m":2550,"region":"Sierra"},
]

CONSTELACIONES = {
    "Starlink":{"planes":24,"sats":12,"inc":53.0,"alt_km":550,"base":44713,"color":"#00aaff","isl":True},
    "OneWeb":  {"planes":12,"sats":9, "inc":87.9,"alt_km":1200,"base":60000,"color":"#00ff88","isl":False},
    "Kuiper":  {"planes":20,"sats":10,"inc":51.9,"alt_km":610, "base":65000,"color":"#ffcc00","isl":True},
}

NIVEL_COLORS = {"NIVEL 1":"#00aaff","NIVEL 2":"#00ff88","NIVEL 3":"#ffcc00"}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILIDADES FÍSICAS
# ═══════════════════════════════════════════════════════════════════════════════
def ecef_to_latlon(x,y,z):
    r=math.sqrt(x**2+y**2+z**2)
    return math.degrees(math.asin(z/r)),math.degrees(math.atan2(y,x)),r-RE_KM

def latlon_to_ecef(lat,lon,alt=0):
    r=RE_KM+alt; phi,lam=math.radians(lat),math.radians(lon)
    return r*math.cos(phi)*math.cos(lam),r*math.cos(phi)*math.sin(lam),r*math.sin(phi)

def dist3d(r1,r2): return math.sqrt(sum((a-b)**2 for a,b in zip(r1,r2)))
def latency_ms(d): return (d/C_KM_S)*1000.0

def haversine(lat1,lon1,lat2,lon2):
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*RE_KM*math.atan2(math.sqrt(a),math.sqrt(1-a))

def elevacion(clat,clon,slat,slon,salt):
    d=2*RE_KM*math.asin(math.sqrt(
        math.sin(math.radians((slat-clat)/2))**2+
        math.cos(math.radians(clat))*math.cos(math.radians(slat))*
        math.sin(math.radians((slon-clon)/2))**2))
    rho=d/RE_KM
    if rho<1e-6: return 90.0
    return math.degrees(math.atan2(math.cos(rho)-RE_KM/(RE_KM+salt),math.sin(rho)))

def hex_rgba(hex_col, alpha=0.15):
    h=hex_col.lstrip('#')
    r,g,b=int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

# ═══════════════════════════════════════════════════════════════════════════════
# PROPAGACIÓN Y GRAFO
# ═══════════════════════════════════════════════════════════════════════════════
def gen_tles(cfg):
    tles=[]
    r=RE_KM+cfg['alt_km']
    n_rev=1440/(2*math.pi*math.sqrt(r**3/GM_KM3)/60)
    for p in range(cfg['planes']):
        raan=(p/cfg['planes'])*360
        for s in range(cfg['sats']):
            M=((s/cfg['sats'])*360+(p/cfg['planes'])*(360/cfg['sats']))%360
            norad=cfg['base']+p*cfg['sats']+s
            l1=f"1 {norad:05d}U 19074A   24015.50000000  .00001500  00000-0  15000-3 0  9990"
            l2=f"2 {norad:05d} {cfg['inc']:8.4f} {raan:8.4f} 0001000  90.0000 {M:8.4f} {n_rev:11.8f}00010"
            tles.append({'l1':l1,'l2':l2,'alt_km':cfg['alt_km'],'inc':cfg['inc']})
    return tles

@st.cache_data(ttl=300, show_spinner=False)
def propagate_const(const_name, time_offset_min=0):
    if not SGP4_OK: return []
    cfg=CONSTELACIONES[const_name]
    tles=gen_tles(cfg)
    t=datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=time_offset_min)
    jd,fr=jday(t.year,t.month,t.day,t.hour,t.minute,t.second)
    sats=[]
    for tle in tles:
        sat=Satrec.twoline2rv(tle['l1'],tle['l2'])
        e,r,v=sat.sgp4(jd,fr)
        if e==0:
            lat,lon,alt=ecef_to_latlon(*r)
            sats.append({**tle,'lat':lat,'lon':lon,'alt_km':alt,'ecef':list(r),'vel':list(v)})
    return sats

def build_isl(sats, max_d=ISL_MAX, k=ISL_K):
    n=len(sats); adj=[[] for _ in range(n)]; edges=[]; used=set()
    for i in range(n):
        dists=[(dist3d(sats[i]['ecef'],sats[j]['ecef']),j) for j in range(n) if j!=i]
        for d,j in sorted(dists)[:k]:
            if d<=max_d:
                key=(min(i,j),max(i,j))
                if key not in used:
                    used.add(key); w=latency_ms(d)
                    adj[i].append((j,w)); adj[j].append((i,w))
                    edges.append({'a':i,'b':j,'w':round(w,3),
                        'la':sats[i]['lat'],'loa':sats[i]['lon'],
                        'lb':sats[j]['lat'],'lob':sats[j]['lon']})
    return adj,edges

@st.cache_data(ttl=300, show_spinner=False)
def compute_graph_metrics(const_name, time_offset_min=0):
    sats=propagate_const(const_name, time_offset_min)
    cfg=CONSTELACIONES[const_name]
    sats_ec=[s for s in sats if haversine(-1.5,-78.0,s['lat'],s['lon'])<2800]
    if not sats_ec: return {}
    if cfg['isl']:
        adj,edges=build_isl(sats_ec)
        G=nx.Graph()
        for i in range(len(sats_ec)): G.add_node(i)
        for e in edges: G.add_edge(e['a'],e['b'],weight=e['w'])
    else:
        G=nx.Graph()
        for i in range(len(sats_ec)): G.add_node(i)
        edges=[]
    comps=list(nx.connected_components(G))
    giant=max(comps,key=len) if comps else set()
    Gc=G.subgraph(giant)
    try:
        avg_path=nx.average_shortest_path_length(Gc,weight='weight') if len(Gc)>1 else 0
    except: avg_path=0
    deg=dict(G.degree())
    return {
        'nodos':G.number_of_nodes(),'aristas':G.number_of_edges(),
        'densidad':round(nx.density(G),4),
        'componentes':len(comps),
        'grado_promedio':round(sum(deg.values())/max(len(deg),1),2),
        'giant_size':len(giant),
        'avg_path_ms':round(avg_path,2),
        'clustering':round(nx.average_clustering(G),4),
        'sats_ec':len(sats_ec),
    }

@st.cache_data(ttl=600, show_spinner=False)
def _cache_path():
    """Ruta del caché compatible con Windows, Mac y Linux."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "aerograf_data_cache.json")

@st.cache_data(ttl=1800, show_spinner=False)
def load_precomputed():
    """
    Carga datos pre-calculados desde caché local.
    Si no existe el caché, los calcula en tiempo real.
    Compatible con Windows, Mac y Linux.
    """
    # Buscar en múltiples rutas
    candidates = [
        _cache_path(),
        os.path.join(os.path.expanduser("~"), "aerograf_data_cache.json"),
        "/tmp/aerograf_data.json",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                continue

    # Si no hay caché → calcular en tiempo real
    return _compute_all_levels()

def _compute_all_levels():
    """Calcula todos los niveles en tiempo real si no hay caché."""
    import math, heapq
    from sgp4.api import Satrec, jday

    t0 = datetime.datetime.now(datetime.timezone.utc)
    time_steps = list(range(0, 95, 5))

    def _gen_tles_local(cfg):
        tles = []
        r = RE_KM + cfg["alt_km"]
        n_rev = 1440 / (2*math.pi*math.sqrt(r**3/GM_KM3)/60)
        for p in range(cfg["planes"]):
            raan = (p/cfg["planes"])*360
            for s in range(cfg["sats"]):
                M = ((s/cfg["sats"])*360+(p/cfg["planes"])*(360/cfg["sats"]))%360
                norad = cfg["base"]+p*cfg["sats"]+s
                l1 = f"1 {norad:05d}U 19074A   24015.50000000  .00001500  00000-0  15000-3 0  9990"
                l2 = f"2 {norad:05d} {cfg['inc']:8.4f} {raan:8.4f} 0001000  90.0000 {M:8.4f} {n_rev:11.8f}00010"
                tles.append({"l1":l1,"l2":l2,"alt_km":cfg["alt_km"],"inc":cfg["inc"]})
        return tles

    def _prop(tles, t):
        jd,fr=jday(t.year,t.month,t.day,t.hour,t.minute,t.second)
        sats=[]
        for tle in tles:
            sat=Satrec.twoline2rv(tle["l1"],tle["l2"])
            e,r,v=sat.sgp4(jd,fr)
            if e==0:
                rm=math.sqrt(sum(x**2 for x in r))
                sats.append({**tle,"lat":math.degrees(math.asin(r[2]/rm)),
                              "lon":math.degrees(math.atan2(r[1],r[0])),
                              "alt_km":rm-RE_KM,"ecef":list(r)})
        return sats

    def _el(clat,clon,slat,slon,salt):
        d=2*RE_KM*math.asin(math.sqrt(
            math.sin(math.radians((slat-clat)/2))**2+
            math.cos(math.radians(clat))*math.cos(math.radians(slat))*
            math.sin(math.radians((slon-clon)/2))**2))
        rho=d/RE_KM
        if rho<1e-6: return 90.0
        return math.degrees(math.atan2(math.cos(rho)-RE_KM/(RE_KM+salt),math.sin(rho)))

    def _lat_ms(d): return d/C_KM_S*1000

    def _latlon_ecef(lat,lon,alt=0):
        r=RE_KM+alt; phi,lam=math.radians(lat),math.radians(lon)
        return r*math.cos(phi)*math.cos(lam),r*math.cos(phi)*math.sin(lam),r*math.sin(phi)

    def _dist3d(r1,r2): return math.sqrt(sum((a-b)**2 for a,b in zip(r1,r2)))

    def _hav(la1,lo1,la2,lo2):
        p1,p2=math.radians(la1),math.radians(la2)
        dp=math.radians(la2-la1); dl=math.radians(lo2-lo1)
        a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return 2*RE_KM*math.atan2(math.sqrt(a),math.sqrt(1-a))

    # ── Nivel 1: visibilidad ──────────────────────────────────────────────────
    nivel1 = {"time_steps":time_steps, "visibilidad":{}}
    for cname, cfg in CONSTELACIONES.items():
        tles = _gen_tles_local(cfg)
        vis_s = {r:[] for r in REGIONES}
        vis_s["TOTAL"] = []
        for dt in time_steps:
            t = t0+datetime.timedelta(minutes=dt)
            sats = _prop(tles,t)
            for rname,rdata in REGIONES.items():
                vis=[s for s in sats if _el(rdata["lat"],rdata["lon"],
                                            s["lat"],s["lon"],s["alt_km"])>=25]
                vis_s[rname].append(len(vis))
            vis_s["TOTAL"].append(len([s for s in sats
                if any(_el(r["lat"],r["lon"],s["lat"],s["lon"],s["alt_km"])>=25
                       for r in REGIONES.values())]))
        nivel1["visibilidad"][cname] = vis_s

    # ── Nivel 2: métricas grafo ───────────────────────────────────────────────
    nivel2 = {"time_steps":time_steps, "metricas":{}}
    for cname, cfg in CONSTELACIONES.items():
        tles = _gen_tles_local(cfg)
        ms_list = []
        for dt in time_steps:
            t = t0+datetime.timedelta(minutes=dt)
            sats = _prop(tles,t)
            sats_ec=[s for s in sats if _hav(-1.5,-78.0,s["lat"],s["lon"])<2800]
            n=len(sats_ec)
            aristas=0
            if cfg["isl"] and n>0:
                used=set()
                for i in range(n):
                    dists=sorted([(_dist3d(sats_ec[i]["ecef"],sats_ec[j]["ecef"]),j)
                                   for j in range(n) if j!=i])
                    for d,j in dists[:4]:
                        if d<=1800:
                            key=(min(i,j),max(i,j))
                            if key not in used: used.add(key); aristas+=1
            ms_list.append({"t":dt,"nodos":n,"aristas":aristas,
                             "densidad":round(2*aristas/(n*(n-1)),4) if n>1 else 0,
                             "giant_size":n,"grado_promedio":round(2*aristas/max(n,1),2),
                             "clustering":0.0,"avg_path_ms":0.0,"componentes":1})
        nivel2["metricas"][cname] = ms_list

    # ── Nivel 3: ICA/ICAT ────────────────────────────────────────────────────
    nivel3 = {"regiones":{}, "puntos_fae":{}}
    for cname, cfg in CONSTELACIONES.items():
        tles = _gen_tles_local(cfg)
        for rname, rdata in REGIONES.items():
            vis_vals=[]
            lat_vals=[]
            for dt in time_steps:
                t = t0+datetime.timedelta(minutes=dt)
                sats = _prop(tles,t)
                vis=[s for s in sats if _el(rdata["lat"],rdata["lon"],
                                            s["lat"],s["lon"],s["alt_km"])>=25]
                vis_vals.append(len(vis))
                if vis:
                    ec_r=_latlon_ecef(rdata["lat"],rdata["lon"])
                    dists=[_dist3d(ec_r,s["ecef"]) for s in vis]
                    lat_vals.append(min(_lat_ms(d) for d in dists))
            ica  = round(min(100, (sum(vis_vals)/len(vis_vals))/15*100), 1)
            icat = round(ica*(1-(sum(lat_vals)/len(lat_vals))/20) if lat_vals else ica, 1)
            if rname not in nivel3["regiones"]: nivel3["regiones"][rname]={}
            nivel3["regiones"][rname][cname] = {
                "ica": ica, "icat": icat,
                "vis_promedio": round(sum(vis_vals)/len(vis_vals),1),
                "lat_promedio": round(sum(lat_vals)/len(lat_vals),2) if lat_vals else None,
            }
        for p in PUNTOS_FAE:
            vis_vals=[]
            for dt in time_steps:
                t = t0+datetime.timedelta(minutes=dt)
                sats = _prop(tles,t)
                vis=[s for s in sats if _el(p["lat"],p["lon"],
                                            s["lat"],s["lon"],s["alt_km"])>=25]
                vis_vals.append(len(vis))
            pid=p["id"]
            if pid not in nivel3["puntos_fae"]: nivel3["puntos_fae"][pid]={}
            nivel3["puntos_fae"][pid][cname]={
                "vis_promedio": round(sum(vis_vals)/len(vis_vals),1),
                "ica": round(min(100,(sum(vis_vals)/len(vis_vals))/15*100),1),
            }

    result = {
        "timestamp": t0.isoformat(),
        "regiones":  {k:{"lat":v["lat"],"lon":v["lon"],"color":v["color"],"desc":v["desc"]}
                      for k,v in REGIONES.items()},
        "puntos_fae": PUNTOS_FAE,
        "nivel1": nivel1,
        "nivel2": nivel2,
        "nivel3": nivel3,
    }

    # Guardar caché para la próxima vez
    try:
        with open(_cache_path(), "w") as f:
            json.dump(result, f)
    except Exception:
        pass

    return result

# ═══════════════════════════════════════════════════════════════════════════════
# PLOTLY — Tema base
# ═══════════════════════════════════════════════════════════════════════════════
THEME=dict(
    paper_bgcolor="#000000", plot_bgcolor="#080808",
    font=dict(color="#ffffff", family="Courier New, monospace"),
    xaxis=dict(gridcolor="#1a1a1a", zerolinecolor="#222222",
               tickfont=dict(color="#888888"),
               title=dict(font=dict(color="#aaaaaa"))),
    yaxis=dict(gridcolor="#1a1a1a", zerolinecolor="#222222",
               tickfont=dict(color="#888888"),
               title=dict(font=dict(color="#aaaaaa"))),
)
THEME_GEO=dict(
    paper_bgcolor="#000000", plot_bgcolor="#080808",
    font=dict(color="#ffffff", family="Courier New, monospace"),
)

def geo_layout():
    return dict(
        scope="world",
        showland=True,    landcolor="#2a2a2a",
        showocean=True,   oceancolor="#050505",
        showlakes=True,   lakecolor="#050505",
        showrivers=False,
        showcountries=True,  countrycolor="#888888", countrywidth=1.2,
        showcoastlines=True, coastlinecolor="#aaaaaa", coastlinewidth=1.5,
        showsubunits=True,   subunitcolor="#666666",  subunitwidth=0.8,
        lonaxis=dict(range=[-95,-73], showgrid=True, gridcolor="#222222", gridwidth=0.5, dtick=5),
        lataxis=dict(range=[ -7,  3], showgrid=True, gridcolor="#222222", gridwidth=0.5, dtick=2),
        bgcolor="#000000",
        showframe=True, framecolor="#555555",
        projection_type="mercator",
        resolution=50,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:10px 0'>
      <div style='font-size:32px'>🛰️</div>
      <div style='font-size:20px;font-weight:700;color:#4fc3f7;letter-spacing:2px'>AEROGRAF-E</div>
      <div style='font-size:11px;color:#aaaaaa;margin-top:4px'>Entorno Aeroespacial Ecuatoriano<br>Grafos Dinámicos LEO · FAE</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("### ⚙️ Parámetros")
    const_sel = st.selectbox("Constelación",list(CONSTELACIONES.keys()),
        format_func=lambda n:f"{'◉' if CONSTELACIONES[n]['isl'] else '○'} {n}")
    time_off = st.slider("⏩ Tiempo orbital (min)",0,95,0,5,
        help="Avanza las posiciones orbitales")
    min_el = st.slider("📡 Elevación mínima (°)",5,45,25,5,
        help="Ángulo mínimo para considerar satélite visible")
    show_isl = st.checkbox("Mostrar ISL",True)
    show_coverage = st.checkbox("Mostrar cobertura",True)

    st.divider()
    st.markdown("### 📐 Definiciones")
    with st.expander("ICA — Índice de Cobertura Aeroespacial"):
        st.markdown("""
        **ICA = (satélites visibles promedio / 15) × 100**

        Mide qué porcentaje del tiempo una región tiene
        cobertura satelital adecuada. 15 sats visibles = ICA 100%.
        """)
    with st.expander("ICAT — ICA ponderado por latencia"):
        st.markdown("""
        **ICAT = ICA × (1 − latencia_promedio / 20ms)**

        Penaliza regiones donde los satélites están en el horizonte
        (mayor distancia = mayor latencia). Mide calidad real, no solo cantidad.
        """)
    with st.expander("Grafo temporal G(T)"):
        st.markdown("""
        ```
        G(T) = {G(t₀), G(t₁), ..., G(tₙ)}
        ```
        Cada G(tᵢ) = (V, E(tᵢ), W(tᵢ))
        - **V** = satélites sobre Ecuador
        - **E** = ISL modelados (dist < 1800 km)
        - **W** = latencia en ms = dist/c
        """)

    st.divider()
    cfg_c=CONSTELACIONES[const_sel]
    st.markdown(f"""
    <div style='background:#0d0d0d;border:1px solid {cfg_c['color']};
    border-radius:8px;padding:12px;font-size:12px'>
    <div style='color:{cfg_c["color"]};font-weight:700;font-size:14px'>{const_sel}</div>
    <div style='color:#aaaaaa;margin-top:4px'>
    Inc: {cfg_c['inc']}° · Alt: {cfg_c['alt_km']}km<br>
    ISL: {'✓' if cfg_c['isl'] else '✗'} · Planos: {cfg_c['planes']} × {cfg_c['sats']}
    </div></div>
    """,unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style='background:linear-gradient(135deg,#000000,#0d0d0d,#000000);
padding:20px 28px;border-radius:12px;border:1px solid #2a2a2a;margin-bottom:20px'>
  <div style='display:flex;align-items:center;gap:16px'>
    <div style='font-size:36px'>🛰️</div>
    <div>
      <div style='font-size:26px;font-weight:700;color:#4fc3f7;letter-spacing:2px'>AEROGRAF-E</div>
      <div style='font-size:13px;color:#aaaaaa'>
        Caracterización del Entorno Aeroespacial Ecuatoriano mediante Grafos Dinámicos de Constelaciones LEO
      </div>
    </div>
    <div style='margin-left:auto;text-align:right;font-size:12px;color:#2a4a6a'>
      UTC: {datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}<br>
      SGP4 · NetworkX · Hypatia<br>
      Fuerza Aérea Ecuatoriana
    </div>
  </div>
  <div style='display:flex;gap:10px;margin-top:14px'>
    <div style='background:rgba(79,195,247,.12);border:1px solid #4fc3f7;border-radius:20px;
    padding:4px 14px;font-size:11px;color:#4fc3f7;font-weight:600'>
    ① OBSERVAR</div>
    <div style='color:#aaaaaa;line-height:24px'>→</div>
    <div style='background:rgba(129,199,132,.12);border:1px solid #81c784;border-radius:20px;
    padding:4px 14px;font-size:11px;color:#81c784;font-weight:600'>
    ② CARACTERIZAR</div>
    <div style='color:#aaaaaa;line-height:24px'>→</div>
    <div style='background:rgba(255,183,77,.12);border:1px solid #ffb74d;border-radius:20px;
    padding:4px 14px;font-size:11px;color:#ffb74d;font-weight:600'>
    ③ CONCIENTIZAR</div>
  </div>
</div>
""",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════
with st.spinner("⚙️ Calculando ICA/ICAT y métricas temporales (primera vez ~30 seg)..."):
    predata = load_precomputed()
if predata:
    st.sidebar.success("✓ Datos listos")
else:
    st.sidebar.error("✗ Sin datos — verifique sgp4")

with st.spinner(f"Propagando {const_sel} con SGP4..."):
    sats_now = propagate_const(const_sel, time_off)
    cfg_now  = CONSTELACIONES[const_sel]
    adj_now, edges_now = (build_isl(sats_now) if cfg_now['isl']
                          else ([[] for _ in range(len(sats_now))],[]))

sats_ec=[s for s in sats_now if haversine(-1.5,-78.0,s['lat'],s['lon'])<2800]

# Métricas instantáneas
with st.spinner("Calculando métricas del grafo..."):
    G_metrics = compute_graph_metrics(const_sel, time_off)

# KPIs
k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("🛰️ Sats totales",   len(sats_now))
k2.metric("🇪🇨 Sobre Ecuador", G_metrics.get('sats_ec',0))
k3.metric("🔗 ISL modelados",    G_metrics.get('aristas',0))
k4.metric("📊 Grado promedio", G_metrics.get('grado_promedio',0))
k5.metric("🕸️ Clustering",     G_metrics.get('clustering',0))
k6.metric("🌐 Componentes",    G_metrics.get('componentes','N/A'))

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# TABS — 3 NIVELES + COMPARACIÓN + METODOLOGÍA
# ═══════════════════════════════════════════════════════════════════════════════
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "① OBSERVAR — Visibilidad Orbital",
    "② CARACTERIZAR — Grafo Dinámico",
    "③ CONCIENTIZAR — ICA/ICAT Regional",
    "🔄 Comparación Multi-Constelación",
    "📋 Metodología",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — NIVEL 1: OBSERVAR
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown(f"""
    <div style='background:rgba(0,255,136,.04);border-left:3px solid #00ff88;
    padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:16px'>
    <strong style='color:#00ff88;letter-spacing:2px'>① NIVEL 1 — OBSERVAR</strong><br>
    <span style='color:#aaaaaa;font-size:13px'>
    ¿Qué satélites pasan sobre Ecuador en este momento y cómo evoluciona su visibilidad?
    </span></div>
    """,unsafe_allow_html=True)

    col_map, col_vis = st.columns([3,2])

    with col_map:
        st.markdown("#### 🌍 Mapa orbital en tiempo real")
        fig_map = go.Figure()
        col_c = cfg_now['color']

        # Satélites
        lats=[s['lat'] for s in sats_now]
        lons=[s['lon'] for s in sats_now]
        fig_map.add_trace(go.Scattergeo(
            lat=lats, lon=lons, mode="markers",
            marker=dict(size=5,color=col_c,opacity=0.6),
            name=f"Satélites {const_sel}",
            hovertemplate="Lat:%{lat:.2f}° Lon:%{lon:.2f}°<extra></extra>",
        ))

        # ISL
        if show_isl and edges_now:
            for e in edges_now[:200]:
                fig_map.add_trace(go.Scattergeo(
                    lat=[e['la'],e['lb'],None],lon=[e['loa'],e['lob'],None],
                    mode="lines",line=dict(width=0.5,color=col_c),
                    opacity=0.2,showlegend=False,
                ))

        # Cobertura footprint por región
        if show_coverage:
            for rname,rdata in REGIONES.items():
                vis=[s for s in sats_now
                     if elevacion(rdata['lat'],rdata['lon'],s['lat'],s['lon'],s['alt_km'])>=min_el]
                if vis:
                    fig_map.add_trace(go.Scattergeo(
                        lat=[rdata['lat']],lon=[rdata['lon']],
                        mode="markers+text",
                        text=[f"{rname} ({len(vis)})"],
                        textposition="top center",
                        marker=dict(size=14,color=rdata['color'],
                                    symbol="circle",opacity=0.85),
                        name=rname,showlegend=True,
                        hovertemplate=f"{rname}: {len(vis)} sats visibles<extra></extra>",
                    ))

        # Puntos FAE
        for p in PUNTOS_FAE:
            vis_p=[s for s in sats_now
                   if elevacion(p['lat'],p['lon'],s['lat'],s['lon'],s['alt_km'])>=min_el]
            fig_map.add_trace(go.Scattergeo(
                lat=[p['lat']],lon=[p['lon']],
                mode="markers+text",
                text=[p['id']],textposition="top right",
                textfont=dict(size=11,color="#ff4444"),
                marker=dict(size=12,color="#ff4444",symbol="triangle-up"),
                name=p['nombre'],
                hovertemplate=f"{p['nombre']}<br>{len(vis_p)} sats visibles<extra></extra>",
            ))

        fig_map.update_layout(
            **THEME_GEO,geo=geo_layout(),
            height=480,margin=dict(l=0,r=0,t=0,b=0),
            legend=dict(bgcolor="#0d0d0d",bordercolor="#2a2a2a",
                        borderwidth=1,font=dict(size=10)),
        )
        st.plotly_chart(fig_map,use_container_width=True)

    with col_vis:
        st.markdown("#### 👁️ Satélites visibles por región")
        for rname,rdata in REGIONES.items():
            vis=[s for s in sats_now
                 if elevacion(rdata['lat'],rdata['lon'],s['lat'],s['lon'],s['alt_km'])>=min_el]
            pct=min(100,len(vis)/15*100)
            st.markdown(f"""
            <div style='margin-bottom:10px'>
              <div style='display:flex;justify-content:space-between;
              color:{rdata['color']};font-size:13px;font-weight:600'>
                <span>📍 {rname}</span><span>{len(vis)} satélites</span>
              </div>
              <div style='background:#111111;border-radius:4px;height:8px;margin-top:4px'>
                <div style='background:{rdata["color"]};width:{pct:.0f}%;
                height:100%;border-radius:4px'></div>
              </div>
              <div style='font-size:10px;color:#aaaaaa;margin-top:2px'>
                Cobertura: {pct:.0f}%
              </div>
            </div>
            """,unsafe_allow_html=True)

        st.divider()
        st.markdown("#### ⏱️ Visibilidad temporal (95 min)")
        if predata:
            fig_ts=go.Figure()
            ts=predata['nivel1']
            for rname,rdata in REGIONES.items():
                vals=ts['visibilidad'][const_sel][rname]
                fig_ts.add_trace(go.Scatter(
                    x=ts['time_steps'],y=vals,mode='lines',
                    name=rname,line=dict(color=rdata['color'],width=1.8),
                ))
            fig_ts.update_layout(**THEME,height=250,
                margin=dict(l=40,r=10,t=10,b=30),
                xaxis_title="min",yaxis_title="Satélites visibles",
                legend=dict(bgcolor="#0d0d0d",bordercolor="#2a2a2a",
                            font=dict(size=9),orientation="h",
                            yanchor="bottom",y=1.02,xanchor="left",x=0),
            )
            st.plotly_chart(fig_ts,use_container_width=True)



        st.divider()
        st.markdown(
            "<div style='font-size:13px;font-weight:700;color:#ffffff;"
            "letter-spacing:2px;margin-bottom:4px'>🕸️ GRAFO DE VISIBILIDAD</div>"
            "<div style='font-size:10px;color:#555555;letter-spacing:1px'>"
            "SATÉLITES (izq) ↔ PUNTOS FAE (der) · Arista = enlace activo · "
            "Grosor = calidad del enlace · Color = punto FAE</div>",
            unsafe_allow_html=True,
        )

        @st.cache_data(ttl=60, show_spinner=False)
        def calc_bipartito(const_name, t_offset, el_min):
            import math
            sats_all = propagate_const(const_name, t_offset)
            col_c    = CONSTELACIONES[const_name]["color"]
            aristas  = []
            ids_vis  = set()
            for pi, p in enumerate(PUNTOS_FAE):
                for si, s in enumerate(sats_all):
                    el = elevacion(p["lat"],p["lon"],s["lat"],s["lon"],s["alt_km"])
                    if el >= el_min:
                        ec = latlon_to_ecef(p["lat"],p["lon"],p["alt_m"]/1000)
                        d  = dist3d(ec, s["ecef"])
                        aristas.append({
                            "si":si,"pi":pi,
                            "el":round(el,1),
                            "ms":round(latency_ms(d),2),
                        })
                        ids_vis.add(si)
            sats_vis   = [sats_all[i] for i in sorted(ids_vis)]
            id_map     = {old:new for new,old in enumerate(sorted(ids_vis))}
            return sats_vis, aristas, id_map, col_c

        sats_v, ars, id_map, col_c = calc_bipartito(const_sel, time_off, min_el)
        n_sv = len(sats_v)
        n_p  = len(PUNTOS_FAE)

        PT_COLS = ["#ff3333","#00aaff","#00ff88","#ffcc00"]

        # Posiciones: satélites columna X=0.15, puntos FAE X=0.85
        # Y distribuido uniformemente con padding
        PAD = 0.05
        def ypos(i, total):
            if total <= 1: return 0.5
            return PAD + i * (1 - 2*PAD) / (total - 1)

        sat_ys = [ypos(i, n_sv) for i in range(n_sv)]
        pt_ys  = [ypos(i, n_p)  for i in range(n_p)]

        fig_b = go.Figure()

        # ── 1. Aristas ────────────────────────────────────────────────────────
        max_ms = max((a["ms"] for a in ars), default=10)
        for a in ars:
            si2 = id_map.get(a["si"], 0)
            pi2 = a["pi"]
            sy2 = sat_ys[si2] if si2 < n_sv else 0.5
            py2 = pt_ys[pi2]  if pi2 < n_p  else 0.5
            # Grosor: mejor enlace (menos latencia) = más grueso
            qual = 1 - (a["ms"] / max(max_ms, 1))
            lw2  = 0.5 + qual * 3.5
            pcol = PT_COLS[pi2 % len(PT_COLS)]
            # Curva bezier simulada con punto intermedio
            xm = 0.5 + (py2 - sy2) * 0.08   # leve curvatura
            fig_b.add_trace(go.Scatter(
                x=[0.15, xm, 0.85],
                y=[sy2,  (sy2+py2)/2, py2],
                mode="lines",
                line=dict(color=pcol, width=lw2, shape="spline"),
                opacity=0.6,
                showlegend=False,
                hovertemplate=(
                    f"SAT-{a['si']:02d} → {PUNTOS_FAE[pi2]['nombre']}<br>"
                    f"El: {a['el']}° | {a['ms']} ms<extra></extra>"
                ),
            ))

        # ── 2. Nodos satélites (izquierda) ────────────────────────────────────
        if sats_v:
            # Colorear por elevación máxima
            max_el_per_sat = {}
            for a in ars:
                si2 = id_map.get(a["si"],0)
                max_el_per_sat[si2] = max(max_el_per_sat.get(si2,0), a["el"])

            fig_b.add_trace(go.Scatter(
                x=[0.15]*n_sv,
                y=sat_ys,
                mode="markers+text",
                marker=dict(
                    size=9,
                    color=[max_el_per_sat.get(i,25) for i in range(n_sv)],
                    colorscale=[[0,"#1a3a2a"],[0.3,"#00aa44"],[0.7,col_c],[1.0,"#ffffff"]],
                    cmin=20, cmax=90,
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="El°", font=dict(color="#666666",size=9)),
                        tickfont=dict(color="#666666",size=8),
                        x=-0.02, thickness=8, len=0.6,
                    ),
                    line=dict(width=0.8, color="#333333"),
                    symbol="circle",
                ),
                text=[f"SAT-{i:02d}" for i in range(n_sv)],
                textposition="middle left",
                textfont=dict(size=7.5, color="#777777"),
                name=f"Satélites {const_sel}",
                hovertemplate=(
                    "SAT-%{pointNumber:02d}<br>"
                    "Lat: %{customdata[0]:.1f}° "
                    "Lon: %{customdata[1]:.1f}°<br>"
                    "Alt: %{customdata[2]:.0f} km<extra></extra>"
                ),
                customdata=[[s["lat"],s["lon"],s["alt_km"]] for s in sats_v],
            ))

        # ── 3. Nodos puntos FAE (derecha) ─────────────────────────────────────
        # Contar conexiones por punto
        conn_per_pt = {pi2:0 for pi2 in range(n_p)}
        for a in ars: conn_per_pt[a["pi"]] = conn_per_pt.get(a["pi"],0)+1

        fig_b.add_trace(go.Scatter(
            x=[0.85]*n_p,
            y=pt_ys,
            mode="markers",
            marker=dict(
                size=[14 + conn_per_pt.get(i,0)*2 for i in range(n_p)],
                color=PT_COLS[:n_p],
                symbol="diamond",
                line=dict(width=1.5, color="#ffffff"),
            ),
            name="Puntos FAE",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Conexiones: %{customdata[0]}<br>"
                "%{customdata[1]}<extra></extra>"
            ),
            text=[p["id"] for p in PUNTOS_FAE],
            customdata=[[conn_per_pt.get(i,0), PUNTOS_FAE[i]["nombre"]]
                        for i in range(n_p)],
        ))

        # ── 4. Etiquetas puntos FAE ───────────────────────────────────────────
        annots = [
            dict(x=0.15, y=1.055, text="<b>SATÉLITES</b>",
                 showarrow=False, xanchor="center",
                 font=dict(size=9, color="#555555")),
            dict(x=0.85, y=1.055, text="<b>ESTACIONES FAE</b>",
                 showarrow=False, xanchor="center",
                 font=dict(size=9, color="#555555")),
        ]
        for i, p in enumerate(PUNTOS_FAE):
            n_conn_p = conn_per_pt.get(i,0)
            annots.append(dict(
                x=0.87, y=pt_ys[i],
                text=(f"<b style='color:{PT_COLS[i]}'>{p['id']}</b> "
                      f"<span style='color:#888888'>{p['nombre']}</span><br>"
                      f"<span style='color:#555555;font-size:9px'>{n_conn_p} enlaces</span>"),
                showarrow=False, xanchor="left", yanchor="middle",
                font=dict(size=10, color=PT_COLS[i]),
            ))

        # ── 5. Layout ─────────────────────────────────────────────────────────
        h_bip = max(400, min(700, n_sv * 24 + 100))
        fig_b.update_layout(
            paper_bgcolor="#000000",
            plot_bgcolor="#050505",
            font=dict(color="#ffffff", family="Courier New, monospace"),
            height=h_bip,
            margin=dict(l=80, r=220, t=50, b=20),
            xaxis=dict(
                showgrid=False, zeroline=False,
                showticklabels=False, range=[0, 1.35],
                showline=False,
            ),
            yaxis=dict(
                showgrid=False, zeroline=False,
                showticklabels=False, range=[-0.05, 1.1],
                showline=False,
            ),
            showlegend=True,
            legend=dict(
                bgcolor="#0a0a0a", bordercolor="#1e1e1e",
                font=dict(size=9), x=0.35, y=-0.04,
                orientation="h",
            ),
            annotations=annots,
        )

        st.plotly_chart(fig_b, use_container_width=True)

        # ── Resumen ───────────────────────────────────────────────────────────
        pts_conectados = len(set(a["pi"] for a in ars))
        lat_min = min((a["ms"] for a in ars), default=0)
        lat_max = max((a["ms"] for a in ars), default=0)
        st.markdown(
            f"<div style='background:#080808;border:1px solid #1e1e1e;"
            f"border-radius:4px;padding:10px 16px;font-size:11px;"
            f"font-family:Courier New,monospace;display:flex;gap:24px;"
            f"align-items:center'>"
            f"<span style='color:#555555'>RESUMEN "
            f"{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')} UTC</span>"
            f"<span>Aristas: <strong style='color:#00ff88'>{len(ars)}</strong></span>"
            f"<span>Satélites: <strong style='color:{col_c}'>{n_sv}</strong></span>"
            f"<span>FAE conectados: <strong style='color:#ffffff'>"
            f"{pts_conectados}/{n_p}</strong></span>"
            f"<span>Lat: <strong style='color:#ffcc00'>{lat_min:.1f}–{lat_max:.1f} ms</strong></span>"
            f"</div>",
            unsafe_allow_html=True,
        )




# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — NIVEL 2: CARACTERIZAR
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"""
    <div style='background:rgba(0,170,255,.04);border-left:3px solid #00aaff;
    padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:16px'>
    <strong style='color:#00aaff;letter-spacing:2px'>② NIVEL 2 — CARACTERIZAR</strong><br>
    <span style='color:#aaaaaa;font-size:13px'>
    ¿Cómo cambia la conectividad y estructura del grafo a lo largo del tiempo?
    Métricas de teoría de grafos aplicadas a la red satelital sobre Ecuador.
    </span></div>
    """,unsafe_allow_html=True)

    # Grafo visual NetworkX → Plotly
    col_g1, col_g2 = st.columns([2,3])

    with col_g1:
        st.markdown("#### 📊 Métricas del grafo actual")
        m=G_metrics
        datos_m=[
            ("Nodos (sats sobre EC)", m.get('sats_ec',0)),
            ("Aristas ISL",           m.get('aristas',0)),
            ("Densidad del grafo",    m.get('densidad',0)),
            ("Componente gigante",    m.get('giant_size',0)),
            ("Grado promedio",        m.get('grado_promedio',0)),
            ("Clustering promedio",   m.get('clustering',0)),
            ("Latencia promedio (ms)",m.get('avg_path_ms',0)),
            ("Componentes conexas",   m.get('componentes','N/A')),
        ]
        for label,val in datos_m:
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;
            padding:8px 0;border-bottom:1px solid #1a3a6a;font-size:13px'>
            <span style='color:#aaaaaa'>{label}</span>
            <strong style='color:#81c784'>{val}</strong></div>
            """,unsafe_allow_html=True)

        st.divider()
        # Interpretación
        dens=m.get('densidad',0)
        clust=m.get('clustering',0)
        st.markdown(f"""
        <div style='background:#0d0d0d;border:1px solid #81c784;
        border-radius:8px;padding:12px;font-size:12px;color:#ffffff'>
        <strong style='color:#81c784'>📌 Interpretación</strong><br><br>
        Densidad <strong>{dens}</strong> →
        {'Red bien conectada' if dens>0.1 else 'Red dispersa (típico LEO)'}<br>
        Clustering <strong>{clust}</strong> →
        {'Nodos forman triángulos' if clust>0.3 else 'Topología de cadena'}<br>
        </div>
        """,unsafe_allow_html=True)

    with col_g2:
        st.markdown("#### 🕸️ Grafo ISL sobre Ecuador — proyección geográfica")
        sats_ec_full=[s for s in sats_now if haversine(-1.5,-78.0,s['lat'],s['lon'])<2800]
        adj_ec,edges_ec=(build_isl(sats_ec_full) if cfg_now['isl']
                         else ([[] for _ in range(len(sats_ec_full))],[]))

        fig_g=go.Figure()
        # ISL edges
        for e in edges_ec:
            sa,sb=sats_ec_full[e['a']],sats_ec_full[e['b']]
            lw=0.5+e['w']/5
            fig_g.add_trace(go.Scattergeo(
                lat=[sa['lat'],sb['lat'],None],
                lon=[sa['lon'],sb['lon'],None],
                mode="lines",
                line=dict(width=lw,color=cfg_now['color']),
                opacity=0.4,showlegend=False,
            ))
        # Satélites (tamaño proporcional al grado)
        if sats_ec_full:
            G_ec=nx.Graph()
            for i in range(len(sats_ec_full)): G_ec.add_node(i)
            for e in edges_ec: G_ec.add_edge(e['a'],e['b'])
            deg=dict(G_ec.degree())
            sizes=[6+deg.get(i,0)*3 for i in range(len(sats_ec_full))]
            fig_g.add_trace(go.Scattergeo(
                lat=[s['lat'] for s in sats_ec_full],
                lon=[s['lon'] for s in sats_ec_full],
                mode="markers",
                marker=dict(size=sizes,color=cfg_now['color'],
                            colorscale='Blues',opacity=0.8,
                            line=dict(width=0.5,color='white')),
                name="Satélite (tamaño=grado)",
                hovertemplate="Grado: %{text}<extra></extra>",
                text=[str(deg.get(i,0)) for i in range(len(sats_ec_full))],
            ))
        # Puntos FAE
        for p in PUNTOS_FAE:
            fig_g.add_trace(go.Scattergeo(
                lat=[p['lat']],lon=[p['lon']],mode="markers+text",
                text=[p['id']],textposition="top right",
                textfont=dict(size=11,color="#ff4444"),
                marker=dict(size=14,color="#ff4444",symbol="triangle-up"),
                name=p['nombre'],showlegend=False,
            ))
        fig_g.update_layout(
            **THEME_GEO,geo=geo_layout(),
            height=420,margin=dict(l=0,r=0,t=0,b=0),
        )
        st.plotly_chart(fig_g,use_container_width=True)

    # Evolución temporal de métricas
    st.markdown("#### 📈 Evolución temporal de métricas del grafo (95 min)")
    if predata:
        fig_met=make_subplots(rows=2,cols=3,
            subplot_titles=["Nodos sobre Ecuador","Aristas ISL","Densidad",
                            "Clustering","Comp. Gigante","Latencia prom. (ms)"],
            vertical_spacing=0.18,horizontal_spacing=0.08)
        metrics_keys=['nodos','aristas','densidad','clustering','giant_size','avg_path_ms']
        row_col=[(1,1),(1,2),(1,3),(2,1),(2,2),(2,3)]
        for cname,cfg in CONSTELACIONES.items():
            ms_list=predata['nivel2']['metricas'][cname]
            ts2=predata['nivel2']['time_steps']
            for (mk,(row,col)) in zip(metrics_keys,row_col):
                vals=[m.get(mk,0) for m in ms_list]
                fig_met.add_trace(go.Scatter(
                    x=ts2,y=vals,mode='lines',name=cname,
                    line=dict(color=CONSTELACIONES[cname]['color'],width=1.8),
                    showlegend=(mk=='nodos'),
                ),row=row,col=col)
        fig_met.update_layout(
            **{k:v for k,v in THEME.items() if k not in ['xaxis','yaxis']},
            height=400,margin=dict(l=40,r=10,t=50,b=30),
            legend=dict(bgcolor="#0d0d0d",bordercolor="#2a2a2a",
                        font=dict(size=10),orientation="h",
                        yanchor="bottom",y=1.04,x=0),
        )
        for i in range(1,7):
            suf='' if i==1 else str(i)
            fig_met.update_xaxes(gridcolor="#1a1a1a", title_text="min", title=dict(font=dict(size=9)))
        st.plotly_chart(fig_met,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — NIVEL 3: CONCIENTIZAR
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown(f"""
    <div style='background:rgba(255,204,0,.04);border-left:3px solid #ffcc00;
    padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:16px'>
    <strong style='color:#ffcc00;letter-spacing:2px'>③ NIVEL 3 — CONCIENTIZAR</strong><br>
    <span style='color:#aaaaaa;font-size:13px'>
    ¿Qué tan dinámico y complejo es el entorno aeroespacial sobre cada región de Ecuador?
    Índices ICA e ICAT como herramienta de conciencia situacional aeroespacial.
    </span></div>
    """,unsafe_allow_html=True)

    @st.cache_data(ttl=600, show_spinner=False)
    def calcular_nivel3_directo():
        """Calcula ICA/ICAT directamente — no depende de predata ni de archivos."""
        import math
        from sgp4.api import Satrec, jday

        t0  = datetime.datetime.now(datetime.timezone.utc)
        ts  = list(range(0, 95, 5))

        def _tles(cfg):
            out=[]
            r=RE_KM+cfg["alt_km"]
            n_rev=1440/(2*math.pi*math.sqrt(r**3/GM_KM3)/60)
            for p in range(cfg["planes"]):
                raan=(p/cfg["planes"])*360
                for s in range(cfg["sats"]):
                    M=((s/cfg["sats"])*360+(p/cfg["planes"])*(360/cfg["sats"]))%360
                    norad=cfg["base"]+p*cfg["sats"]+s
                    l1=f"1 {norad:05d}U 19074A   24015.50000000  .00001500  00000-0  15000-3 0  9990"
                    l2=f"2 {norad:05d} {cfg['inc']:8.4f} {raan:8.4f} 0001000  90.0000 {M:8.4f} {n_rev:11.8f}00010"
                    out.append({"l1":l1,"l2":l2,"alt_km":cfg["alt_km"],"inc":cfg["inc"]})
            return out

        def _prop(tles, t):
            jd,fr=jday(t.year,t.month,t.day,t.hour,t.minute,t.second)
            sats=[]
            for tle in tles:
                sat=Satrec.twoline2rv(tle["l1"],tle["l2"])
                e,r,v=sat.sgp4(jd,fr)
                if e==0:
                    rm=math.sqrt(sum(x**2 for x in r))
                    sats.append({**tle,
                        "lat":math.degrees(math.asin(r[2]/rm)),
                        "lon":math.degrees(math.atan2(r[1],r[0])),
                        "alt_km":rm-RE_KM,"ecef":list(r)})
            return sats

        def _el(clat,clon,slat,slon,salt):
            d=2*RE_KM*math.asin(math.sqrt(
                math.sin(math.radians((slat-clat)/2))**2+
                math.cos(math.radians(clat))*math.cos(math.radians(slat))*
                math.sin(math.radians((slon-clon)/2))**2))
            rho=d/RE_KM
            if rho<1e-6: return 90.0
            return math.degrees(math.atan2(math.cos(rho)-RE_KM/(RE_KM+salt),math.sin(rho)))

        def _lat_ms(d): return d/C_KM_S*1000
        def _dist3d(r1,r2): return math.sqrt(sum((a-b)**2 for a,b in zip(r1,r2)))
        def _ecef(lat,lon,alt=0):
            r=RE_KM+alt; phi,lam=math.radians(lat),math.radians(lon)
            return r*math.cos(phi)*math.cos(lam),r*math.cos(phi)*math.sin(lam),r*math.sin(phi)

        resultado = {"regiones":{}, "puntos_fae":{}}

        for cname, cfg in CONSTELACIONES.items():
            tles = _tles(cfg)
            # ICA por región
            for rname, rdata in REGIONES.items():
                vis_v=[]; lat_v=[]
                for dt in ts:
                    t=t0+datetime.timedelta(minutes=dt)
                    sats=_prop(tles,t)
                    vis=[s for s in sats
                         if _el(rdata["lat"],rdata["lon"],s["lat"],s["lon"],s["alt_km"])>=25]
                    vis_v.append(len(vis))
                    if vis:
                        ec=_ecef(rdata["lat"],rdata["lon"])
                        lat_v.append(min(_lat_ms(_dist3d(ec,s["ecef"])) for s in vis))
                avg = sum(vis_v)/len(vis_v) if vis_v else 0
                ica  = round(min(100, avg/15*100), 1)
                icat = round(ica*(1-(sum(lat_v)/len(lat_v))/20) if lat_v else ica, 1)
                if rname not in resultado["regiones"]:
                    resultado["regiones"][rname] = {}
                resultado["regiones"][rname][cname] = {
                    "ica": ica, "icat": icat,
                    "vis_promedio": round(avg, 1),
                    "lat_promedio": round(sum(lat_v)/len(lat_v),2) if lat_v else 0,
                }
            # ICA por punto FAE
            for p in PUNTOS_FAE:
                vis_v=[]
                for dt in ts:
                    t=t0+datetime.timedelta(minutes=dt)
                    sats=_prop(tles,t)
                    vis=[s for s in sats
                         if _el(p["lat"],p["lon"],s["lat"],s["lon"],s["alt_km"])>=25]
                    vis_v.append(len(vis))
                avg=sum(vis_v)/len(vis_v) if vis_v else 0
                pid=p["id"]
                if pid not in resultado["puntos_fae"]:
                    resultado["puntos_fae"][pid] = {}
                resultado["puntos_fae"][pid][cname] = {
                    "vis_promedio": round(avg,1),
                    "ica": round(min(100, avg/15*100), 1),
                }
        return resultado

    with st.spinner("⚙️ Calculando ICA/ICAT por región (~30 seg primera vez)..."):
        n3 = calcular_nivel3_directo()

    if n3 and n3.get("regiones"):
        # ── Mapa ICA + Radar ──────────────────────────────────────────────────
        col_heat, col_radar = st.columns([3,2])

        with col_heat:
            st.markdown("#### 🗺️ Mapa ICA/ICAT por región de Ecuador")
            fig_ica = go.Figure()
            for rname, rdata in REGIONES.items():
                d = n3["regiones"].get(rname,{}).get(const_sel,{})
                ica_v  = d.get("ica",0)
                icat_v = d.get("icat",0)
                vis_v  = d.get("vis_promedio",0)
                fig_ica.add_trace(go.Scattergeo(
                    lat=[rdata["lat"]], lon=[rdata["lon"]],
                    mode="markers+text",
                    text=[f"ICA={ica_v:.0f}"],
                    textposition="top center",
                    textfont=dict(size=11, color="white"),
                    marker=dict(
                        size=20+ica_v/5,
                        color=ica_v,
                        colorscale="RdYlGn",
                        cmin=0, cmax=100,
                        line=dict(width=1.5, color="white"),
                        showscale=True,
                        colorbar=dict(
                            title=dict(text="ICA", font=dict(color="#cccccc")),
                            tickfont=dict(color="#cccccc"),
                        ),
                    ),
                    name=rname,
                    hovertemplate=(
                        f"<b>{rname}</b><br>"
                        f"ICA: {ica_v:.1f}<br>"
                        f"ICAT: {icat_v:.1f}<br>"
                        f"Sats̄: {vis_v}<extra></extra>"
                    ),
                ))
            for p in PUNTOS_FAE:
                d_p = n3["puntos_fae"].get(p["id"],{}).get(const_sel,{})
                ica_p = d_p.get("ica",0)
                fig_ica.add_trace(go.Scattergeo(
                    lat=[p["lat"]], lon=[p["lon"]],
                    mode="markers+text",
                    text=[p["id"]],
                    textposition="bottom right",
                    textfont=dict(size=10, color="#ff3333"),
                    marker=dict(size=12, color="#ff3333", symbol="triangle-up"),
                    showlegend=False,
                    hovertemplate=f"<b>{p['nombre']}</b><br>ICA: {ica_p:.1f}<extra></extra>",
                ))
            fig_ica.update_layout(
                **THEME_GEO, geo=geo_layout(),
                height=420, margin=dict(l=0,r=0,t=0,b=0),
            )
            st.plotly_chart(fig_ica, use_container_width=True)

        with col_radar:
            st.markdown("#### 🕸️ Radar ICA — todas las constelaciones")
            categorias = list(REGIONES.keys())
            fig_radar  = go.Figure()
            for cname, cfg in CONSTELACIONES.items():
                vals = [n3["regiones"].get(r,{}).get(cname,{}).get("ica",0)
                        for r in categorias]
                vals_c = vals + [vals[0]]
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals_c,
                    theta=categorias+[categorias[0]],
                    fill="toself",
                    name=cname,
                    line=dict(color=cfg["color"], width=2),
                    fillcolor=hex_rgba(cfg["color"], 0.1),
                ))
            fig_radar.update_layout(
                **{k:v for k,v in THEME.items() if k not in ["xaxis","yaxis"]},
                polar=dict(
                    bgcolor="#0a0a0a",
                    radialaxis=dict(
                        visible=True, range=[0,100],
                        gridcolor="#1a1a1a",
                        tickfont=dict(color="#666666", size=9),
                    ),
                    angularaxis=dict(
                        gridcolor="#1a1a1a",
                        tickfont=dict(color="#cccccc", size=10),
                    ),
                ),
                height=380,
                legend=dict(bgcolor="#0d0d0d", bordercolor="#2a2a2a",
                            font=dict(size=10)),
                margin=dict(l=40,r=40,t=20,b=20),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # ── Tabla ICA/ICAT completa ───────────────────────────────────────────
        st.markdown("#### 📋 Tabla ICA/ICAT — todas las regiones")
        rows = []
        for rname, rdata_geo in REGIONES.items():
            row = {"Región": rname, "Descripción": rdata_geo["desc"]}
            for cname in CONSTELACIONES:
                d = n3["regiones"].get(rname,{}).get(cname,{})
                row[f"ICA {cname}"]  = f"{d.get('ica',0):.1f}"
                row[f"ICAT {cname}"] = f"{d.get('icat',0):.1f}"
                row[f"Sats̄ {cname}"] = f"{d.get('vis_promedio',0):.1f}"
            rows.append(row)
        df_ica = pd.DataFrame(rows).set_index("Región")
        st.dataframe(df_ica, use_container_width=True)

        # ── Barras ICA por región ─────────────────────────────────────────────
        st.markdown("#### 📊 ICA comparativo por región")
        fig_bar = go.Figure()
        for cname, cfg in CONSTELACIONES.items():
            ica_v = [n3["regiones"].get(r,{}).get(cname,{}).get("ica",0)
                     for r in REGIONES]
            fig_bar.add_trace(go.Bar(
                name=cname,
                x=list(REGIONES.keys()),
                y=ica_v,
                marker_color=cfg["color"],
                opacity=0.85,
                text=[f"{v:.0f}" for v in ica_v],
                textposition="outside",
                textfont=dict(color="#ffffff", size=11),
            ))
        fig_bar.add_hline(
            y=70, line_dash="dash", line_color="#ff3333",
            annotation_text="Umbral operacional (70)",
            annotation_font_color="#ff3333",
        )
        fig_bar.update_layout(
            **THEME,
            barmode="group",
            yaxis_title="ICA (%)", yaxis_range=[0,115],
            margin=dict(l=50,r=20,t=20,b=40), height=350,
            legend=dict(bgcolor="#0d0d0d", bordercolor="#2a2a2a",
                        font=dict(size=11)),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # ── Puntos FAE ICA ────────────────────────────────────────────────────
        st.markdown("#### 📍 ICA en Puntos FAE")
        cols_fae = st.columns(4)
        for p, col_f in zip(PUNTOS_FAE, cols_fae):
            with col_f:
                col_f.markdown(
                    f"<div style='font-size:13px;font-weight:700;"
                    f"color:#ff3333;text-align:center;margin-bottom:8px'>"
                    f"{p['id']} — {p['nombre']}</div>",
                    unsafe_allow_html=True,
                )
                for cname, cfg in CONSTELACIONES.items():
                    d = n3["puntos_fae"].get(p["id"],{}).get(cname,{})
                    ica  = d.get("ica",0)
                    vis  = d.get("vis_promedio",0)
                    col_f.markdown(
                        f"<div style='background:#0c0c0c;border:1px solid {cfg['color']};"
                        f"border-radius:4px;padding:8px;margin-bottom:6px;text-align:center'>"
                        f"<div style='color:{cfg['color']};font-size:11px;"
                        f"font-weight:700;letter-spacing:1px'>{cname}</div>"
                        f"<div style='font-size:22px;font-weight:700;"
                        f"color:{cfg['color']}'>{ica:.0f}%</div>"
                        f"<div style='font-size:10px;color:#666666'>"
                        f"{vis:.1f} sats promedio</div></div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.error("No se pudieron calcular los datos. Verifique que sgp4 está instalado: pip install sgp4")

with tab4:
    st.markdown("#### 🔄 Comparación simultánea de las 3 constelaciones")
    cols_comp=st.columns(3)
    for (cname,cfg),col_c in zip(CONSTELACIONES.items(),cols_comp):
        with col_c:
            sats_c=propagate_const(cname,time_off)
            ec_c=[s for s in sats_c if haversine(-1.5,-78.0,s['lat'],s['lon'])<2800]
            m_c=compute_graph_metrics(cname,time_off)
            vis_total=sum(1 for r in REGIONES.values()
                         for s in sats_c
                         if elevacion(r['lat'],r['lon'],s['lat'],s['lon'],s['alt_km'])>=min_el)
            col_c.markdown(f"""
            <div style='border:2px solid {cfg["color"]};border-radius:12px;
            padding:16px;background:{hex_rgba(cfg["color"],0.05)}'>
            <div style='font-size:20px;font-weight:700;color:{cfg["color"]}'>{cname}</div>
            <div style='font-size:11px;color:#aaaaaa;margin-bottom:12px'>{cfg.get("inc","")}° · {cfg.get("alt_km","")}km · ISL:{"✓" if cfg["isl"] else "✗"}</div>
            """,unsafe_allow_html=True)
            col_c.metric("Sats sobre Ecuador", len(ec_c))
            col_c.metric("ISL modelados", m_c.get('aristas',0))
            col_c.metric("Clustering", m_c.get('clustering',0))
            col_c.metric("Lat. prom. (ms)", m_c.get('avg_path_ms',0))
            if predata:
                ica_avg=np.mean([predata['nivel3']['regiones'][r][cname]['ica']
                                 for r in REGIONES])
                col_c.metric("ICA promedio Ecuador", f"{ica_avg:.1f}%")
            col_c.markdown("</div>",unsafe_allow_html=True)

    if predata:
        st.divider()
        st.markdown("#### 📈 Evolución de satélites visibles totales — 3 constelaciones")
        fig_comp=go.Figure()
        for cname,cfg in CONSTELACIONES.items():
            ts_c=predata['nivel1']
            vals=predata['nivel1']['visibilidad'][cname]['TOTAL']
            fig_comp.add_trace(go.Scatter(
                x=ts_c['time_steps'],y=vals,mode='lines+markers',
                name=cname,marker=dict(size=4),
                line=dict(color=cfg['color'],width=2.5),
                fill='tozeroy',fillcolor=hex_rgba(cfg['color'],0.06),
            ))
        fig_comp.update_layout(**THEME,height=320,
            xaxis_title="Tiempo (min)",yaxis_title="Satélites visibles (cualquier región)",
            margin=dict(l=50,r=20,t=20,b=40),
            legend=dict(bgcolor="#0d0d0d",bordercolor="#2a2a2a",font=dict(size=11)),
        )
        st.plotly_chart(fig_comp,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — METODOLOGÍA
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("#### 📋 Marco metodológico de AEROGRAF-E")
    col_m1,col_m2=st.columns(2)
    with col_m1:
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

    with col_m2:
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

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center;color:#2a4a6a;font-size:11px;padding:8px'>
  <strong style='color:#aaaaaa'>AEROGRAF-E</strong> ·
  SGP4 + NetworkX + Dijkstra Temporal + Plotly ·
  Parámetros FCC: Starlink/OneWeb/Kuiper ·
  Basado en Hypatia (IMC'20, ACM) ·
  Fuerza Aérea Ecuatoriana · 2026
</div>
""",unsafe_allow_html=True)
