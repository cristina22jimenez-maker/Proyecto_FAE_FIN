"""
graph.py — Construcción y análisis del grafo ISL temporal
══════════════════════════════════════════════════════════
Construye el grafo de Inter-Satellite Links (ISL) sobre
los satélites propagados, calcula métricas NetworkX y
genera series temporales del grafo dinámico G(T).

Importa SOLO desde orbital.py — sin duplicar física.
"""

import datetime
import heapq
from typing import Optional
import networkx as nx

try:
    from .orbital import (
        dist3d, latency_ms, propagate,
        gen_tles, haversine,
    )
except ImportError:  # modo directo: archivo ejecutado desde la raíz
    from orbital import (
        dist3d, latency_ms, propagate,
        gen_tles, haversine,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DEL GRAFO ISL
# ═══════════════════════════════════════════════════════════════════════════════
ISL_MAX_KM = 1_800.0    # Distancia máxima de un ISL (km)
ISL_K      = 4          # Vecinos más cercanos a considerar
EXACT_PATH_LIMIT = 200  # Evita todos-contra-todos en constelaciones grandes
PATH_SAMPLE_SIZE = 64


def build_isl(sats: list,
              max_d: float = ISL_MAX_KM,
              k: int = ISL_K) -> tuple:
    """
    Construye el grafo ISL (Inter-Satellite Links) para una lista de satélites.

    Algoritmo:
        Para cada satélite i, calcula los k vecinos más cercanos.
        Si la distancia ≤ max_d, agrega la arista con peso = latencia (ms).

    Retorna:
        adj   : lista de adyacencia [(vecino, latencia_ms)]
        edges : lista de dicts {a, b, w_ms, dist_km, lat_a, lon_a, lat_b, lon_b}
    """
    n    = len(sats)
    adj  = [[] for _ in range(n)]
    edges = []
    used  = set()

    for i in range(n):
        dists = sorted(
            [(dist3d(sats[i]["ecef"], sats[j]["ecef"]), j)
             for j in range(n) if j != i]
        )
        for d, j in dists[:k]:
            if d > max_d:
                continue
            key = (min(i, j), max(i, j))
            if key in used:
                continue
            used.add(key)
            w = latency_ms(d)
            adj[i].append((j, w))
            adj[j].append((i, w))
            edges.append({
                "a":     i,
                "b":     j,
                "w":     round(w, 3),
                "w_ms":  round(w, 3),
                "dist_km": round(d, 1),
                "lat_a": sats[i]["lat"],
                "lon_a": sats[i]["lon"],
                "lat_b": sats[j]["lat"],
                "lon_b": sats[j]["lon"],
                "la": sats[i]["lat"],
                "loa": sats[i]["lon"],
                "lb": sats[j]["lat"],
                "lob": sats[j]["lon"],
            })
    return adj, edges


def build_networkx(sats: list, edges: list) -> nx.Graph:
    """
    Convierte la lista de adyacencia en un grafo NetworkX.
    Agrega atributos de posición a cada nodo.
    """
    G = nx.Graph()
    for i, s in enumerate(sats):
        G.add_node(i, lat=s["lat"], lon=s["lon"], alt=s["alt_km"])
    for e in edges:
        G.add_edge(e["a"], e["b"], weight=e["w_ms"], dist=e["dist_km"])
    return G


# ═══════════════════════════════════════════════════════════════════════════════
# MÉTRICAS DEL GRAFO
# ═══════════════════════════════════════════════════════════════════════════════
def graph_metrics(G: nx.Graph) -> dict:
    """
    Calcula métricas estándar de teoría de grafos para el grafo ISL.

    Métricas:
        nodos           : número de satélites (nodos)
        aristas         : número de ISL activos
        densidad        : fracción de aristas posibles que existen
        componentes     : número de componentes conexas
        giant_size      : tamaño de la componente gigante
        grado_promedio  : grado medio de los nodos
        grado_max       : grado máximo
        clustering      : coeficiente de clustering promedio
        avg_path_ms     : latencia promedio de camino más corto (ms)
    """
    if G.number_of_nodes() == 0:
        return {k: 0 for k in ["nodos","aristas","densidad","componentes",
                                "giant_size","grado_promedio","grado_max",
                                "clustering","avg_path_ms"]}

    comps = list(nx.connected_components(G))
    giant = max(comps, key=len) if comps else set()
    Gc    = G.subgraph(giant)
    deg   = dict(G.degree())

    try:
        if len(Gc) <= 1:
            avg_path = 0.0
        elif len(Gc) <= EXACT_PATH_LIMIT:
            avg_path = nx.average_shortest_path_length(Gc, weight="weight")
        else:
            nodes = sorted(Gc.nodes())[:PATH_SAMPLE_SIZE]
            distances = [
                distance
                for source in nodes
                for target, distance in nx.single_source_dijkstra_path_length(
                    Gc, source, weight="weight"
                ).items()
                if target != source
            ]
            avg_path = sum(distances) / len(distances) if distances else 0.0
    except Exception:
        avg_path = 0.0

    return {
        "nodos":          G.number_of_nodes(),
        "aristas":        G.number_of_edges(),
        "densidad":       round(nx.density(G), 4),
        "componentes":    len(comps),
        "giant_size":     len(giant),
        "grado_promedio": round(sum(deg.values()) / max(len(deg), 1), 2),
        "grado_max":      max(deg.values()) if deg else 0,
        "clustering":     round(nx.average_clustering(G), 4),
        "avg_path_ms":    round(avg_path, 2),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTING — DIJKSTRA
# ═══════════════════════════════════════════════════════════════════════════════
def dijkstra(adj: list, n: int, src: int, dst: int) -> tuple:
    """
    Dijkstra con cola de prioridad sobre la lista de adyacencia.

    Retorna (path, costo_ms):
        path     : lista de índices de nodos en la ruta óptima
        costo_ms : latencia total del camino (ms)
        Si no existe camino: ([], inf)
    """
    INF  = float("inf")
    dist = [INF] * n
    prev = [-1]  * n
    dist[src] = 0.0
    pq  = [(0.0, src)]
    vis = [False] * n

    while pq:
        d, u = heapq.heappop(pq)
        if vis[u]:
            continue
        vis[u] = True
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))

    path = []
    cur  = dst
    while cur >= 0:
        path.append(int(cur))
        cur = prev[cur]
    path.reverse()

    if not path or path[0] != src:
        return [], float("inf")
    return path, float(dist[dst])


# ═══════════════════════════════════════════════════════════════════════════════
# EVOLUCIÓN TEMPORAL DEL GRAFO G(T)
# ═══════════════════════════════════════════════════════════════════════════════
def serie_metricas(tles: list,
                   t0: datetime.datetime,
                   time_steps: list,
                   region_center: tuple = (-1.5, -78.0),
                   radio_km: float = 2_800.0,
                   has_isl: bool = True) -> list:
    """
    Calcula las métricas del grafo ISL en cada instante de time_steps.

    Solo considera satélites dentro de radio_km del centro de Ecuador.
    Para constelaciones sin ISL (OneWeb), retorna métricas vacías.

    Retorna lista de dicts con métricas + campo 't' (offset en minutos).
    """
    clat, clon = region_center
    resultado  = []

    for dt_min in time_steps:
        t    = t0 + datetime.timedelta(minutes=float(dt_min))
        sats = propagate(tles, t)

        # Filtrar satélites sobre Ecuador
        sats_ec = [s for s in sats
                   if haversine(clat, clon, s["lat"], s["lon"]) < radio_km]

        if has_isl and sats_ec:
            adj, edges = build_isl(sats_ec)
            G           = build_networkx(sats_ec, edges)
            m           = graph_metrics(G)
        else:
            m = {
                "nodos": len(sats_ec), "aristas": 0, "densidad": 0.0,
                "componentes": max(1, len(sats_ec)), "giant_size": len(sats_ec),
                "grado_promedio": 0.0, "grado_max": 0,
                "clustering": 0.0, "avg_path_ms": 0.0,
            }
        m["t"] = dt_min
        resultado.append(m)

    return resultado
