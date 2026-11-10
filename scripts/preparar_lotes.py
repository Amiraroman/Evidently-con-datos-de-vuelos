"""Divide vuelos_nyc_2013.csv en lotes. El CSV original no se modifica.

Uso:
    python scripts/preparar_lotes.py datos/vuelos_nyc_2013.csv

Genera datos/referencia.csv, datos/control.csv, datos/nuevo.csv y, para la
primera publicación, datos/actual.csv (copia de control.csv).
"""
import shutil
import sys
from pathlib import Path

import pandas as pd

COLUMNAS = [
    "vuelo_id", "fecha", "origen", "destino",
    "demora_salida_min", "demora_llegada_min", "distancia_millas", "lote",
]
LOTES = ["referencia", "control", "nuevo"]


def main(origen: str) -> int:
    df = pd.read_csv(origen, dtype=str, keep_default_na=False)
    destino = Path("datos")
    destino.mkdir(exist_ok=True)
    for lote in LOTES:
        sub = df[df["lote"] == lote][COLUMNAS]
        ruta = destino / f"{lote}.csv"
        sub.to_csv(ruta, index=False, lineterminator="\n")
        print(f"{ruta}: {len(sub)} filas")
        if len(sub) != 12000:
            print(f"  ADVERTENCIA: se esperaban 12000 filas", file=sys.stderr)
    shutil.copyfile(destino / "control.csv", destino / "actual.csv")
    print("datos/actual.csv = copia de control.csv (primera publicación)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python scripts/preparar_lotes.py ruta/al/vuelos_nyc_2013.csv")
    sys.exit(main(sys.argv[1]))
