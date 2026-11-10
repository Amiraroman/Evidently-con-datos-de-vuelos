"""Pruebas de validación con datos pequeños e independientes."""
import pandas as pd

from scripts.validar import COLUMNAS, validar_dataframe, validar_archivo

BASE = {
    "vuelo_id": "1", "fecha": "2013-01-15", "origen": "JFK", "destino": "LAX",
    "demora_salida_min": "5", "demora_llegada_min": "10",
    "distancia_millas": "2475", "lote": "referencia",
}


def df_de(*filas):
    return pd.DataFrame([{**BASE, **f} for f in filas], dtype=str)


def validar(df, lotes=None):
    return validar_dataframe(df, "prueba.csv", lotes)


def test_registro_valido():
    assert validar(df_de({})) == []


def test_demora_negativa_y_cero_validas():
    df = df_de({"vuelo_id": "1", "demora_salida_min": "-12", "demora_llegada_min": "0"})
    assert validar(df) == []


def test_encabezado_faltante():
    df = df_de({}).drop(columns=["distancia_millas"])
    errores = validar(df)
    assert len(errores) == 1 and "distancia_millas" in errores[0]


def test_fecha_invalida():
    errores = validar(df_de({"fecha": "2013-02-30"}))
    assert len(errores) == 1
    assert "fila 2" in errores[0] and "'fecha'" in errores[0]


def test_fecha_de_otro_mes():
    errores = validar(df_de({"fecha": "2013-02-10"}))  # lote referencia = enero
    assert any("no corresponde al lote" in e for e in errores)


def test_identificador_duplicado():
    errores = validar(df_de({"vuelo_id": "7"}, {"vuelo_id": "7"}))
    assert len(errores) == 1
    assert "fila 3" in errores[0] and "duplicado" in errores[0]


def test_distancia_invalida():
    for malo in ("0", "-5", "abc", "10.5"):
        errores = validar(df_de({"distancia_millas": malo}))
        assert len(errores) == 1 and "'distancia_millas'" in errores[0], malo


def test_origen_y_destino_invalidos():
    errores = validar(df_de({"origen": "SFO", "destino": "lax"}))
    assert len(errores) == 2


def test_lote_no_permitido_en_actual():
    errores = validar(df_de({}), lotes={"control", "nuevo"})
    assert any("no permitido" in e for e in errores)


def test_archivo_sin_filas(tmp_path):
    ruta = tmp_path / "referencia.csv"
    ruta.write_text(",".join(COLUMNAS) + "\n")
    errores = validar_archivo(ruta)
    assert errores and "no tiene filas" in errores[0]
