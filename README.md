# Monitoreo de demoras en vuelos de Nueva York (CI/CD + Evidently)

Valida lotes mensuales de vuelos de 2013 (JFK, LGA, EWR), compara las demoras con enero usando
Evidently y publica el informe del último lote válido en GitHub Pages.

- **Autor:** COMPLETAR NOMBRE
- **Fuente:** [nycflights13](https://github.com/tidyverse/nycflights13)
- **Sitio:** COMPLETAR URL de GitHub Pages

## Estructura

```
datos/                  referencia.csv (enero, fijo), control.csv (febrero), nuevo.csv (julio), actual.csv
scripts/preparar_lotes.py   divide vuelos_nyc_2013.csv en lotes
scripts/validar.py          reglas de validación (archivo, fila y campo del error)
scripts/generar_sitio.py    informe Evidently + index.html en sitio/
tests/test_validacion.py    pruebas automatizadas
.github/workflows/despliegue.yml   CI (pruebas, validación, build) y CD (GitHub Pages)
```

## Uso local

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1) Preparar lotes (una sola vez; el CSV original no se modifica)
python scripts/preparar_lotes.py ruta/a/vuelos_nyc_2013.csv

# 2) Pruebas
python -m pytest -q

# 3) Validar los CSV del proyecto (termina con código 1 si hay errores)
python scripts/validar.py datos/referencia.csv datos/actual.csv

# 4) Generar el sitio en sitio/ (abre sitio/index.html)
python scripts/generar_sitio.py
```

## Escenarios

| # | Acción sobre `datos/actual.csv` | Resultado esperado |
|---|---|---|
| 1 | `copy datos/control.csv datos/actual.csv` (febrero) | CI y CD en verde; portada y informe: febrero vs enero |
| 2 | `copy datos/nuevo.csv datos/actual.csv` (julio) | Portada con julio y nuevo commit; informe julio vs enero |
| 3 | Cambiar `distancia_millas` de una fila a `0` | CI falla, CD omitido, Pages conserva julio |
| 4 | Restaurar la distancia original | CI y CD en verde, julio con nuevo commit |

(En Linux/macOS usa `cp` en lugar de `copy`.)

## Reglas de validación

- Ocho encabezados exactos y al menos una fila.
- `vuelo_id`: entero positivo y único dentro del archivo.
- `fecha`: AAAA-MM-DD válida y del mes/año del lote (referencia = 2013-01, control = 2013-02, nuevo = 2013-07).
- `origen` ∈ {JFK, LGA, EWR}; `destino`: tres letras mayúsculas.
- Demoras: enteros (cero y negativos válidos). `distancia_millas`: entero positivo.
- `referencia.csv` solo contiene el lote `referencia`; `actual.csv` solo `control` o `nuevo`.

Un **error de validación** bloquea la publicación (CI falla y CD se omite). Un **cambio de
distribución** (drift en Evidently) no bloquea: se publica y se revisa por aeropuerto o ruta.

## Configuración de GitHub Pages

En el repositorio: *Settings → Pages → Build and deployment → Source: GitHub Actions*.
