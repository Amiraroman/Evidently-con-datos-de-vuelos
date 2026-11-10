"""Validación de lotes de vuelos.

Uso:
    python scripts/validar.py                       # valida referencia.csv y actual.csv
    python scripts/validar.py datos/actual.csv ...  # valida archivos concretos

Termina con código 1 si hay errores; cada error identifica archivo, fila y campo.
"""
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

COLUMNAS = [
    "vuelo_id", "fecha", "origen", "destino",
    "demora_salida_min", "demora_llegada_min", "distancia_millas", "lote",
]
ORIGENES = {"JFK", "LGA", "EWR"}
# lote -> (año, mes) esperado en `fecha`
MES_DEL_LOTE = {"referencia": (2013, 1), "control": (2013, 2), "nuevo": (2013, 7)}
LOTES_PERMITIDOS = {
    "referencia.csv": {"referencia"},
    "actual.csv": {"control", "nuevo"},
}
RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_DESTINO = re.compile(r"^[A-Z]{3}$")
RE_ENTERO = re.compile(r"^[+-]?\d+$")


def _es_entero(valor) -> bool:
    return bool(RE_ENTERO.match(str(valor).strip()))


def validar_dataframe(df: pd.DataFrame, nombre: str, lotes_permitidos=None) -> list[str]:
    """Devuelve la lista de errores de un DataFrame leído como texto (dtype=str)."""
    errores: list[str] = []

    faltantes = [c for c in COLUMNAS if c not in df.columns]
    if faltantes:
        errores.append(f"{nombre}: faltan encabezados {faltantes}")
        return errores  # sin encabezados no se puede validar el resto
    if len(df) == 0:
        errores.append(f"{nombre}: el archivo no tiene filas de datos")
        return errores

    def err(i, campo, msg):
        # i es el índice 0-based del DataFrame; +2 = número de línea en el archivo
        errores.append(f"{nombre}: fila {i + 2}, campo '{campo}': {msg}")

    vistos: dict[str, int] = {}
    for i, fila in df.iterrows():
        # vuelo_id: entero positivo y único
        vid = str(fila["vuelo_id"]).strip()
        if not (_es_entero(vid) and int(vid) > 0):
            err(i, "vuelo_id", f"debe ser un entero positivo (valor: {vid!r})")
        elif vid in vistos:
            err(i, "vuelo_id", f"duplicado (ya aparece en la fila {vistos[vid] + 2})")
        else:
            vistos[vid] = i

        # lote
        lote = str(fila["lote"]).strip()
        if lote not in MES_DEL_LOTE:
            err(i, "lote", f"lote desconocido {lote!r}")
        elif lotes_permitidos is not None and lote not in lotes_permitidos:
            err(i, "lote", f"{lote!r} no permitido aquí; se esperaba {sorted(lotes_permitidos)}")

        # fecha: válida y del mes/año del lote
        f = str(fila["fecha"]).strip()
        if not RE_FECHA.match(f):
            err(i, "fecha", f"formato inválido, se espera AAAA-MM-DD (valor: {f!r})")
        else:
            try:
                d = date.fromisoformat(f)
            except ValueError:
                err(i, "fecha", f"fecha inexistente (valor: {f!r})")
            else:
                if lote in MES_DEL_LOTE and (d.year, d.month) != MES_DEL_LOTE[lote]:
                    a, m = MES_DEL_LOTE[lote]
                    err(i, "fecha", f"{f} no corresponde al lote {lote!r} ({a}-{m:02d})")

        # origen / destino
        o = str(fila["origen"]).strip()
        if o not in ORIGENES:
            err(i, "origen", f"debe ser JFK, LGA o EWR (valor: {o!r})")
        d_ = str(fila["destino"]).strip()
        if not RE_DESTINO.match(d_):
            err(i, "destino", f"debe tener tres letras mayúsculas (valor: {d_!r})")

        # demoras: enteros (cero y negativos válidos)
        for campo in ("demora_salida_min", "demora_llegada_min"):
            v = str(fila[campo]).strip()
            if not _es_entero(v):
                err(i, campo, f"debe ser un entero (valor: {v!r})")

        # distancia: entero positivo
        dist = str(fila["distancia_millas"]).strip()
        if not (_es_entero(dist) and int(dist) > 0):
            err(i, "distancia_millas", f"debe ser un entero positivo (valor: {dist!r})")

    return errores


def validar_archivo(ruta, lotes_permitidos=None) -> list[str]:
    ruta = Path(ruta)
    if not ruta.exists():
        return [f"{ruta}: el archivo no existe"]
    try:
        df = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    except Exception as e:  # CSV ilegible
        return [f"{ruta}: no se pudo leer el CSV ({e})"]
    if lotes_permitidos is None:
        lotes_permitidos = LOTES_PERMITIDOS.get(ruta.name)
    return validar_dataframe(df, str(ruta), lotes_permitidos)


def main(argv: list[str]) -> int:
    archivos = argv or ["datos/referencia.csv", "datos/actual.csv"]
    errores: list[str] = []
    for a in archivos:
        e = validar_archivo(a)
        print(f"{'OK   ' if not e else 'ERROR'} {a}")
        errores += e
    if errores:
        print(f"\nSe encontraron {len(errores)} error(es):", file=sys.stderr)
        for e in errores[:50]:
            print(f"  - {e}", file=sys.stderr)
        if len(errores) > 50:
            print(f"  ... y {len(errores) - 50} más", file=sys.stderr)
        return 1
    print("Validación correcta.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
