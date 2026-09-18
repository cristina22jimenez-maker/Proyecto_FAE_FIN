"""passes.py — Calculo de pasos (ventanas de visibilidad) por punto.

Responde a la pregunta "que activos son visibles desde un punto de Ecuador
durante un periodo dado". Reutiliza propagate()/elevacion() de orbital.py,
sin volver a implementar fisica orbital.
"""

import datetime

try:
    from .orbital import propagate, elevacion
except ImportError:  # modo directo: archivo ejecutado desde la raiz
    from orbital import propagate, elevacion


def calcular_pasos(tles: list, punto: dict,
                   t0: datetime.datetime,
                   horizonte_min: float,
                   paso_min: float = 1.0,
                   min_el: float = 10.0) -> list[dict]:
    """
    Detecta pasos (entradas/salidas de visibilidad) de una lista de TLEs
    sobre un punto, muestreando cada paso_min minutos durante horizonte_min.

    Es una deteccion por muestreo (no analitica): la precision de inicio/fin
    depende de paso_min. Un satelite se propaga una sola vez por instante
    para todos los TLEs (no uno por satelite), para mantener el costo lineal
    incluso con catalogos reales de miles de objetos.

    Retorna lista de dicts, ordenada por inicio:
        {satelite, inicio_min, fin_min, duracion_min, elevacion_max}
    """
    n_steps = max(1, int(horizonte_min // paso_min) + 1)
    activos: dict[str, dict] = {}
    pasos = []

    for i in range(n_steps):
        t_off = i * paso_min
        t = t0 + datetime.timedelta(minutes=t_off)
        sats = propagate(tles, t)
        visibles_ahora = set()

        for sat in sats:
            el = elevacion(punto["lat"], punto["lon"], sat["lat"], sat["lon"], sat["alt_km"])
            if el < min_el:
                continue
            nombre = sat.get("name", "SAT")
            visibles_ahora.add(nombre)
            if nombre not in activos:
                activos[nombre] = {"inicio_min": t_off, "max_el": el, "max_el_min": t_off}
            elif el > activos[nombre]["max_el"]:
                activos[nombre]["max_el"] = el
                activos[nombre]["max_el_min"] = t_off

        for nombre in list(activos):
            if nombre not in visibles_ahora:
                info = activos.pop(nombre)
                pasos.append(_cerrar_paso(nombre, info, t_off, t0))

    for nombre, info in activos.items():
        pasos.append(_cerrar_paso(nombre, info, horizonte_min, t0))

    pasos.sort(key=lambda p: p["inicio_min"])
    return pasos


def _cerrar_paso(nombre: str, info: dict, fin_min: float, t0: datetime.datetime) -> dict:
    inicio_min = info["inicio_min"]
    return {
        "satelite": nombre,
        "inicio": (t0 + datetime.timedelta(minutes=inicio_min)).strftime("%H:%M"),
        "fin": (t0 + datetime.timedelta(minutes=fin_min)).strftime("%H:%M"),
        "inicio_min": inicio_min,
        "fin_min": fin_min,
        "duracion_min": round(fin_min - inicio_min, 1),
        "elevacion_max": round(info["max_el"], 1),
    }
