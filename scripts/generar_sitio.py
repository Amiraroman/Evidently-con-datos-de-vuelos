"""Genera el sitio (index.html + informe de Evidently) comparando actual.csv con referencia.csv.

Uso:  python scripts/generar_sitio.py
Variables opcionales: GITHUB_SHA (commit), AUTOR.
"""
import html
import os
import subprocess
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

from evidently import DataDefinition, Dataset, Report  # noqa: E402
from evidently.presets import DataDriftPreset  # noqa: E402

AUTOR = os.environ.get("AUTOR", "Autor: COMPLETAR NOMBRE")
FUENTE = "nycflights13 (vuelos de 2013 desde JFK, LGA y EWR), muestra de 12.000 registros por mes"
FUENTE_URL = "https://github.com/tidyverse/nycflights13"
COLS = ["demora_salida_min", "demora_llegada_min"]
MESES = {"referencia": "enero", "control": "febrero", "nuevo": "julio"}
SITIO = Path("sitio")


def commit_actual() -> str:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha[:7]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "local (sin commit)"


def extraer_drift(snapshot) -> dict:
    """Busca en el resultado de Evidently el valor de drift de cada columna."""
    resumen = {}
    for m in snapshot.dict().get("metrics", []):
        nombre = str(m.get("metric_name", "")) + str(m.get("metric_id", ""))
        cfg = m.get("config", {})
        col = cfg.get("column")
        if "ValueDrift" in nombre and col in COLS:
            resumen[col] = {
                "valor": m.get("value"),
                "umbral": cfg.get("threshold"),
                "metodo": cfg.get("method"),
            }
    return resumen


def main() -> None:
    ref = pd.read_csv("datos/referencia.csv")
    act = pd.read_csv("datos/actual.csv")
    lote = act["lote"].iloc[0]
    mes_act, mes_ref = MESES[lote], MESES["referencia"]
    nombre_informe = f"informe_{mes_act}_vs_{mes_ref}.html"

    definicion = DataDefinition(numerical_columns=COLS)
    ds_ref = Dataset.from_pandas(ref[COLS], data_definition=definicion)
    ds_act = Dataset.from_pandas(act[COLS], data_definition=definicion)
    # Misma configuración para febrero y julio (sin parámetros específicos del lote).
    informe = Report([DataDriftPreset(columns=COLS)])
    snap = informe.run(current_data=ds_act, reference_data=ds_ref)

    SITIO.mkdir(exist_ok=True)
    for viejo in SITIO.glob("informe_*.html"):
        viejo.unlink()
    snap.save_html(str(SITIO / nombre_informe))

    drift = extraer_drift(snap)
    filas = ""
    for c in COLS:
        d = drift.get(c, {})
        v = d.get("valor")
        u = d.get("umbral")
        if isinstance(v, (int, float)) and isinstance(u, (int, float)):
            estado = "drift detectado" if v > u else "sin drift"
            detalle = f"{v:.3f} (umbral {u})"
        else:
            estado, detalle = "ver informe", "-"
        filas += (
            f"<tr><td>{c}</td><td>{ref[c].median():.0f}</td><td>{act[c].median():.0f}</td>"
            f"<td>{detalle}</td><td>{estado}</td></tr>\n"
        )

    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pagina = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitoreo de demoras en vuelos de Nueva York</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;color:#1b1f23;line-height:1.5}}
h1{{font-size:1.6rem}} table{{border-collapse:collapse;width:100%;margin:1rem 0}}
th,td{{border:1px solid #d0d7de;padding:.5rem .7rem;text-align:left}} th{{background:#f6f8fa}}
.kpi{{display:flex;gap:1rem;flex-wrap:wrap}} .kpi div{{background:#f6f8fa;border-radius:8px;padding:.8rem 1rem;flex:1;min-width:150px}}
.kpi b{{display:block;font-size:1.4rem}} footer{{margin-top:2rem;color:#57606a;font-size:.9rem}}
</style></head><body>
<h1>Demoras de vuelos de Nueva York (2013)</h1>
<p>Último lote publicado y comparación con enero de 2013 (referencia).</p>
<div class="kpi">
<div>Último mes publicado<b>{html.escape(mes_act.capitalize())} 2013</b></div>
<div>Registros analizados<b>{len(act):,}</b></div>
<div>Commit<b>{html.escape(commit_actual())}</b></div>
<div>Generado<b style="font-size:1rem">{ahora}</b></div>
</div>
<h2>Medianas y deriva frente a enero</h2>
<table>
<tr><th>Variable</th><th>Mediana enero</th><th>Mediana {html.escape(mes_act)}</th><th>Puntaje de drift</th><th>Resultado</th></tr>
{filas}</table>
<p><a href="{nombre_informe}">Informe de Evidently: {html.escape(mes_act)} vs {html.escape(mes_ref)}</a></p>
<p>Un cambio de distribución indica que conviene investigar en qué aeropuertos o rutas se concentra; no implica que los datos sean inválidos.</p>
<footer>Autor: {html.escape(AUTOR)} · Fuente: <a href="{FUENTE_URL}">{html.escape(FUENTE)}</a></footer>
</body></html>
"""
    (SITIO / "index.html").write_text(pagina, encoding="utf-8")
    (SITIO / ".nojekyll").write_text("")
    print(f"Sitio generado en {SITIO}/ : index.html y {nombre_informe}")


if __name__ == "__main__":
    main()
