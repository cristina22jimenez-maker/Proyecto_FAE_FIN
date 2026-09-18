"""
registro_fae.py — Registro real del Centro de Operaciones Espaciales (COE)
═══════════════════════════════════════════════════════════════════════════
Transcripción del "Consolidado de seguimiento de activos espaciales,
semana del 05 al 11 de septiembre de 2026" (COAO / Centro de Operaciones
Espaciales). Cada entrada corresponde a un paso visible registrado por el
COE para un activo espacial sobre Ecuador.

Campos:
    fecha              : fecha del registro (YYYY-MM-DD)
    turno              : turno de observación registrado por el COE
    nombre             : nombre del activo espacial
    operador_pais      : país operador del activo
    norad              : identificador NORAD (catálogo), como texto
    pasos_visibles_hl  : ventana de paso visible registrada, hora local (HL, UTC-5)
    estado             : estado operativo reportado por el COE
"""

REGISTRO_FAE = [
    {"fecha": "2026-09-05", "turno": "07:00-23:00", "nombre": "GALAPAGOS-UTE", "operador_pais": "ECUADOR", "norad": "67279", "pasos_visibles_hl": "08:11-08:23", "estado": "ACTIVO"},
    {"fecha": "2026-09-05", "turno": "07:00-23:00", "nombre": "AMAZONIA 1", "operador_pais": "BRASIL", "norad": "47699", "pasos_visibles_hl": "10:36-10:51", "estado": "ACTIVO"},
    {"fecha": "2026-09-05", "turno": "07:00-23:00", "nombre": "NEE-01", "operador_pais": "ECUADOR", "norad": "39151", "pasos_visibles_hl": "16:02-16:13", "estado": "INACTIVO"},
    {"fecha": "2026-09-05", "turno": "07:00-23:00", "nombre": "FASAT-C", "operador_pais": "CHILE", "norad": "38011", "pasos_visibles_hl": "21:55-22:02", "estado": "ACTIVO"},

    {"fecha": "2026-09-06", "turno": "07:00-23:00", "nombre": "AMAZONIA 1", "operador_pais": "BRASIL", "norad": "47699", "pasos_visibles_hl": "09:59-10:11", "estado": "ACTIVO"},
    {"fecha": "2026-09-06", "turno": "07:00-23:00", "nombre": "PERUSAT-01", "operador_pais": "PERU", "norad": "41770", "pasos_visibles_hl": "10:39-10:52", "estado": "ACTIVO"},
    {"fecha": "2026-09-06", "turno": "07:00-23:00", "nombre": "GALAPAGOS-UTE", "operador_pais": "ECUADOR", "norad": "67279", "pasos_visibles_hl": "11:17-11:27", "estado": "ACTIVO"},
    {"fecha": "2026-09-06", "turno": "07:00-23:00", "nombre": "NEE-02", "operador_pais": "ECUADOR", "norad": "39441", "pasos_visibles_hl": "13:33-13:45", "estado": "ACTIVO"},

    {"fecha": "2026-09-07", "turno": "07:00-23:00", "nombre": "PERUSAT-01", "operador_pais": "PERU", "norad": "41770", "pasos_visibles_hl": "10:52-10:54", "estado": "ACTIVO"},
    {"fecha": "2026-09-07", "turno": "07:00-23:00", "nombre": "GALAPAGOS-UTE", "operador_pais": "ECUADOR", "norad": "67279", "pasos_visibles_hl": "11:15-11:25", "estado": "ACTIVO"},
    {"fecha": "2026-09-07", "turno": "07:00-23:00", "nombre": "NEE-01", "operador_pais": "ECUADOR", "norad": "39151", "pasos_visibles_hl": "16:00-16:20", "estado": "ACTIVO"},
    {"fecha": "2026-09-07", "turno": "07:00-23:00", "nombre": "SAOCOM 1B", "operador_pais": "ARGENTINA", "norad": "46265", "pasos_visibles_hl": "16:37-16:41", "estado": "ACTIVO"},
    {"fecha": "2026-09-07", "turno": "07:00-23:00", "nombre": "VRSS-2", "operador_pais": "VENEZUELA", "norad": "42954", "pasos_visibles_hl": "21:09-21:19", "estado": "ACTIVO"},

    {"fecha": "2026-09-08", "turno": "07:00-23:00", "nombre": "VRSS-2", "operador_pais": "VENEZUELA", "norad": "42954", "pasos_visibles_hl": "08:53-08:56", "estado": "ACTIVO"},
    {"fecha": "2026-09-08", "turno": "07:00-23:00", "nombre": "NEE-02", "operador_pais": "ECUADOR", "norad": "39441", "pasos_visibles_hl": "14:06-14:09", "estado": "ACTIVO"},
    {"fecha": "2026-09-08", "turno": "07:00-23:00", "nombre": "GALAPAGOS-UTE", "operador_pais": "ECUADOR", "norad": "67279", "pasos_visibles_hl": "22:39-22:50", "estado": "ACTIVO"},

    {"fecha": "2026-09-09", "turno": "07:00-23:00", "nombre": "PERUSAT-01", "operador_pais": "PERU", "norad": "41770", "pasos_visibles_hl": "10:37-10:39", "estado": "ACTIVO"},
    {"fecha": "2026-09-09", "turno": "07:00-23:00", "nombre": "GALAPAGOS-UTE", "operador_pais": "ECUADOR", "norad": "67279", "pasos_visibles_hl": "10:35-10:36", "estado": "INACTIVO"},
    {"fecha": "2026-09-09", "turno": "07:00-23:00", "nombre": "NEE-02", "operador_pais": "ECUADOR", "norad": "39441", "pasos_visibles_hl": "14:19-14:21", "estado": "INACTIVO"},
    {"fecha": "2026-09-09", "turno": "07:00-23:00", "nombre": "NEE-01", "operador_pais": "ECUADOR", "norad": "39151", "pasos_visibles_hl": "16:31-16:34", "estado": "ACTIVO"},
    {"fecha": "2026-09-09", "turno": "07:00-23:00", "nombre": "SSOT", "operador_pais": "CHILE", "norad": "38011", "pasos_visibles_hl": "21:35-21:36", "estado": "ACTIVO"},
]
