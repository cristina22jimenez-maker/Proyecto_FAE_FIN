# Integración AEROGRAF-E — DATOS REALES

## 1. Estructura

Colocar estos archivos en la misma carpeta que `aerograf_e_v2.py`:

```text
AEROGRAF-E/
├── aerograf_e_v2.py
├── activos_espaciales.csv
└── activos_reales.py
```

## 2. Importar el módulo

En `aerograf_e_v2.py`, después de los imports actuales, agregar:

```python
from activos_reales import cargar_activos, render_tab_datos_reales
```

## 3. Cargar el CSV

Después de:

```python
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
```

agregar:

```python
ACTIVOS_CSV = os.path.join(PROJECT_DIR, "activos_espaciales.csv")
activos_reales_df = cargar_activos(ACTIVOS_CSV)
```

## 4. Agregar la nueva pestaña

Reemplazar:

```python
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "① OBSERVAR", "② CARACTERIZAR", "③ CONCIENTIZAR",
    "🔄 COMPARACIÓN", "📋 METODOLOGÍA",
])
```

por:

```python
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⓪ DATOS REALES",
    "① OBSERVAR",
    "② CARACTERIZAR",
    "③ CONCIENTIZAR",
    "🔄 COMPARACIÓN",
    "📋 METODOLOGÍA",
])
```

## 5. Renderizar la pestaña

Antes de:

```python
with tab1:
```

agregar:

```python
with tab0:
    render_tab_datos_reales(activos_reales_df)
```

## 6. Corregir el texto de metodología

En `render_methodology()`, reemplazar:

```python
st.markdown("**Pipeline**\n\n1. TLEs reales desde `starlink.tle`.\n2. Propagación SGP4.\n3. Grafo temporal.\n4. Métricas NetworkX.\n5. ICA/ICAT y Plotly.")
```

por:

```python
st.markdown(
    "**Fuentes y pipeline**\n\n"
    "1. Registro histórico de activos espaciales y TLE de referencia.\n"
    "2. TLE de constelaciones para escenarios LEO.\n"
    "3. Propagación orbital mediante SGP4.\n"
    "4. Grafo temporal y métricas NetworkX.\n"
    "5. ICA/ICAT y visualización interactiva.\n\n"
    "**Distinción:** los activos del registro documental se muestran como "
    "datos históricos de referencia; las constelaciones LEO se utilizan "
    "en escenarios de análisis y simulación."
)
```

## 7. Cambiar el mensaje del sidebar

Reemplazar:

```python
st.sidebar.info(
    "Datos actuales cargados desde starlink.tle. "
    "El análisis histórico se calculará aparte para no bloquear la aplicación."
)
```

por:

```python
st.sidebar.info(
    "AEROGRAF-E integra un registro histórico de activos espaciales "
    "y escenarios de constelaciones LEO. "
    "Los datos del registro no representan seguimiento en tiempo real."
)
```

## 8. Nueva narrativa del stand

La pestaña queda:

```text
⓪ DATOS REALES
      ↓
① OBSERVAR
      ↓
② CARACTERIZAR
      ↓
③ CONCIENTIZAR
```

Interpretación:

- DATOS REALES → ¿Qué activos fueron registrados y cuándo?
- OBSERVAR → ¿Qué satélites podemos analizar sobre Ecuador?
- CARACTERIZAR → ¿Cómo se estructura el grafo?
- CONCIENTIZAR → ¿Cómo cambia el entorno aeroespacial?

## 9. Validación futura

Una segunda fase puede tomar cada TLE del CSV, propagarlo con SGP4 y
comparar la ventana calculada por AEROGRAF-E con `paso_inicio_hl` y
`paso_fin_hl`. No se debe llamar "validación" hasta realizar esa
comparación cuantitativa.

## 10. Dependencia

`activos_reales.py` usa `pandas` y `streamlit`, que ya forman parte del
entorno de la aplicación. No añade una dependencia orbital nueva.
