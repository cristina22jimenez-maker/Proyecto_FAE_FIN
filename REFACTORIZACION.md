# Refactorizacion modular de AEROGRAF-E

## Estructura propuesta

```text
aerograf_e.py                 # Interfaz Streamlit y composicion de vistas
aerograf_src/
  __init__.py                 # API publica del paquete
  config.py                   # Regiones, puntos FAE y constelaciones
  orbital.py                  # Geometria, TLEs y propagacion SGP4
  visibility.py               # Visibilidad y enlaces satelite-estacion
  graph.py                    # ISL, NetworkX, Dijkstra y series temporales
  indices.py                  # ICA, ICAT y calculo regional
  data.py                     # Cache y preparacion de los tres niveles
  visualization.py            # Temas y layouts Plotly
aerograf_data_cache.json      # Cache generado, no logica de dominio
```

## Responsabilidades

- `config.py`: datos estables de configuracion. No importa Streamlit ni Plotly.
- `orbital.py`: unicamente fisica orbital y SGP4.
- `visibility.py`: recibe satelites propagados y calcula elevacion, distancia y latencia.
- `graph.py`: transforma satelites en grafos y calcula metricas.
- `indices.py`: calcula ICA/ICAT a partir de las APIs de orbital y visibilidad.
- `data.py`: coordina los modulos cientificos y persiste resultados en JSON.
- `visualization.py`: contiene colores, temas y layouts reutilizables.
- `aerograf_e.py`: controla Streamlit y presenta los datos; no debe conocer detalles de SGP4.

## Importacion y uso

Desde otro script ubicado en la raiz del proyecto:

```python
from aerograf_src import (
    CONSTELACIONES,
    gen_tles,
    propagate,
    sats_visibles,
    build_isl,
    graph_metrics,
    calcular_ica,
)

import datetime

tles = gen_tles(CONSTELACIONES["Starlink"])
sats = propagate(tles, datetime.datetime.now(datetime.timezone.utc))
visibles = sats_visibles(sats, -0.15, -78.31, min_el=25)
adj, edges = build_isl(sats)
```

Para cargar el analisis completo:

```python
from aerograf_src import load_precomputed

data = load_precomputed(".")
```

La aplicacion Streamlit se ejecuta igual:

```text
streamlit run aerograf_e.py
```

## Comparacion de lineas

Conteo aproximado de lineas de codigo Python, sin contar cache generado:

| Responsabilidad | Antes | Despues |
|---|---:|---:|
| `aerograf_e.py` | 1,330 | 1,330 en esta primera fase |
| Fisica y propagacion reutilizable | incluida en la app | `orbital.py` |
| Visibilidad | incluida en la app | `visibility.py` |
| Grafo | incluida en la app | `graph.py` |
| ICA/ICAT | incluida en la app | `indices.py` |
| Cache y calculo masivo | incluida en la app | `data.py` |
| Configuracion | incluida en la app | `config.py` |

La primera fase mantiene los adaptadores y bloques antiguos necesarios para no cambiar la UI de golpe. Los adaptadores ya delegan en `aerograf_src`; la segunda fase puede eliminar los bloques legacy sin cambiar la interfaz.

## Decisiones de diseno

1. `aerograf_src` tiene un nombre valido como paquete Python; se elimino la dependencia de una carpeta llamada `version del`.
2. Los modulos cientificos no importan Streamlit. Esto permite probarlos con Python normal y reutilizarlos en notebooks o servicios.
3. `data.py` coordina el calculo masivo; la UI solo solicita datos y renderiza resultados.
4. `__init__.py` ofrece una API pequena y estable, evitando imports internos repetidos.
5. Se conservaron las claves publicas de regiones (`Amazonía`, `Galápagos`, etc.) para mantener compatibilidad con caches y graficos existentes.
6. El cache se trata como una optimizacion: si no existe o es invalido, los datos se recalculan.

## Verificacion realizada

- `python -m compileall -q aerograf_src`
- `python -m py_compile aerograf_e.py`
- Propagacion SGP4 de Starlink: 288 satelites generados y propagados.
- Calculo reducido de los tres niveles con `time_steps=[0]`.
