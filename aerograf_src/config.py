"""Configuracion y datos de referencia de AEROGRAF-E."""

import datetime

REGIONES = {
    "Costa": {"lat": -1.5, "lon": -80.0, "color": "#00aaff", "desc": "Costa Pacifica"},
    "Sierra": {"lat": -1.8, "lon": -78.6, "color": "#00ff88", "desc": "Cordillera Andina"},
    "Amazonía": {"lat": -1.5, "lon": -76.5, "color": "#ffcc00", "desc": "Región Amazónica"},
    "Galápagos": {"lat": -0.95, "lon": -90.97, "color": "#ff44aa", "desc": "Archipiélago"},
    "Frontera N": {"lat": 0.3, "lon": -77.5, "color": "#ff6600", "desc": "Frontera Norte"},
    "Frontera S": {"lat": -4.5, "lon": -79.0, "color": "#cc44ff", "desc": "Frontera Sur"},
}

PUNTOS_FAE = [
    {"id": "P1", "nombre": "Checa/Yaruqui", "lat": -0.1454, "lon": -78.3105, "alt_m": 2550, "region": "Sierra"},
    {"id": "P2", "nombre": "CIDFAE", "lat": -1.2138, "lon": -78.5764, "alt_m": 2850, "region": "Sierra"},
    {"id": "P3", "nombre": "El Arenal/GYE", "lat": -2.1620, "lon": -79.8784, "alt_m": 10, "region": "Costa"},
    {"id": "P4", "nombre": "Antenas FAE", "lat": -0.1460, "lon": -78.3107, "alt_m": 2550, "region": "Sierra"},
]

CONSTELACIONES = {
    "Starlink": {
        "planes": 24,
        "sats": 12,
        "inc": 53.0,
        "alt_km": 550,
        "base": 44713,
        "color": "#00aaff",
        "isl": True,
    },
    "OneWeb": {
        "planes": 12,
        "sats": 9,
        "inc": 87.9,
        "alt_km": 1200,
        "base": 60000,
        "color": "#00ff88",
        "isl": False,
    },
    "Kuiper": {
        "planes": 20,
        "sats": 10,
        "inc": 51.9,
        "alt_km": 610,
        "base": 65000,
        "color": "#ffcc00",
        "isl": True,
    },
}

TIME_STEPS = list(range(0, 95, 5))
REGION_CENTER = (-1.5, -78.0)
REGION_RADIUS_KM = 2800.0

# Modo temporal histórico: semana de seguimiento real del COE (05-11 sep 2026).
MODO_HISTORICO = {
    "inicio": datetime.datetime(2026, 9, 5, 0, 0, tzinfo=datetime.timezone.utc),
    "fin": datetime.datetime(2026, 9, 11, 23, 59, tzinfo=datetime.timezone.utc),
    "paso_min": 30,
}
