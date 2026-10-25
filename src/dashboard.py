"""Entrega final: dashboard en una sola página HTML (Plotly.js).

Criterio de diseño: "si el ganadero solo tuviera 5 minutos, ¿qué necesita ver?"
Por eso el orden de la página sigue el orden de las preguntas que él se haría:

  1. ¿A qué vaca reviso?        -> número grande + ranking (lo primero que se ve)
  2. ¿A qué hora la reviso?     -> minutos con temperatura alta por hora del día,
                                   alineado con el calor del corral (THI)
  3. ¿Cómo afecta el calor al descanso de todo el grupo?  -> contexto, más chico
  4. Detalle para el veterinario -> la serie completa de 14 días (Avance 3)

Reglas de color (las mismas desde el Avance 1):
  naranja = solo la vaca seleccionada, gris = el resto, azul = el umbral.

Un solo selector arriba cambia la vaca en las cuatro gráficas. Python prepara
los datos y los mete en la página como JSON; la página solo los dibuja.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from datos import UMBRAL_TEMP, VACAS
from estilo import GRAY, LGRAY, BLUE, ORANGE, INK, MUTED

PLANTILLA = Path(__file__).with_name("dashboard_plantilla.html")


def _lista(s, dec=2):
    """Serie -> lista para JSON (los huecos quedan como null)."""
    return [None if pd.isna(x) else round(float(x), dec) for x in s]


def _datos_dashboard(L: dict, T: dict) -> dict:
    cbt = L["cbt"].assign(h=lambda d: d.t.dt.hour)
    altos = cbt[cbt.temperature_C >= UMBRAL_TEMP]

    # 1) ranking: minutos arriba del umbral y en cuántos días pasó
    minutos = altos.groupby("cow").size().reindex(VACAS, fill_value=0)
    dias = altos.groupby("cow").t.apply(lambda s: s.dt.date.nunique()).reindex(VACAS, fill_value=0)

    # 2) por hora del día: minutos altos de cada vaca y THI promedio del corral
    por_hora = altos.groupby(["cow", "h"]).size().unstack(fill_value=0).reindex(
        index=VACAS, columns=range(24), fill_value=0)
    thi = L["thi"]
    thi_hora = thi.groupby(thi.t.dt.hour).THI.mean().reindex(range(24))

    # 3) descanso vs calor (solo días completos)
    e = T["echada"].merge(T["thi_dia"], on="d")

    # 4) serie horaria suavizada de cada vaca + mediana y rango de las otras 9
    th = T["temp_hora"].pivot(index="t", columns="cow", values="temp_suav")[VACAS]
    serie = {}
    for v in VACAS:
        otras = th.drop(columns=v)
        serie[v] = {"vaca": _lista(th[v]), "med": _lista(otras.median(axis=1)),
                    "min": _lista(otras.min(axis=1)), "max": _lista(otras.max(axis=1))}
    thi_serie = T["thi_hora"].set_index("t").THI.reindex(th.index)

    pend, corte = np.polyfit(e.thi_promedio, e.horas_echada, 1)
    return {
        "vacas": VACAS, "umbral": UMBRAL_TEMP,
        "minutos": minutos.tolist(), "dias": dias.tolist(),
        "n_dias": len(L["dias_completos"]) + 1,          # 14 días de registro (13 completos)
        "por_hora": por_hora.values.tolist(),
        "thi_hora": thi_hora.round(1).tolist(),
        "echada": {"vaca": e.cow.tolist(), "thi": e.thi_promedio.round(1).tolist(),
                   "horas": e.horas_echada.round(1).tolist(),
                   "fecha": pd.to_datetime(e.d).dt.strftime("%d/%m").tolist()},
        "tendencia": {"pendiente": round(pend, 3), "corte": round(corte, 2),
                      "r": round(e[["thi_promedio", "horas_echada"]].corr().iloc[0, 1], 2),
                      "x": [round(e.thi_promedio.min(), 1), round(e.thi_promedio.max(), 1)]},
        "serie_t": th.index.strftime("%Y-%m-%d %H:%M").tolist(),
        "serie": serie,
        "serie_thi": _lista(thi_serie, 1),
        "kpi": {"temp_mediana": round(cbt.temperature_C.median(), 2),
                "pct_alto": round(100 * (cbt.temperature_C >= UMBRAL_TEMP).mean(), 2),
                "echada_mediana": round(e.horas_echada.median(), 1),
                "atipicos": int(e.dia_atipico.sum())},
        "colores": {"gris": GRAY, "gris_claro": LGRAY, "azul": BLUE, "naranja": ORANGE,
                    "tinta": INK, "tenue": MUTED},
    }


def generar(L: dict, T: dict, archivo, vaca_inicial: str = "C09") -> dict:
    """Escribe el dashboard en `archivo` y regresa las cifras que muestra."""
    d = _datos_dashboard(L, T)
    d["vaca_inicial"] = vaca_inicial
    html = PLANTILLA.read_text(encoding="utf-8").replace(
        "/*__DATOS__*/null", json.dumps(d, ensure_ascii=False, allow_nan=False))
    # Plotly va dentro del mismo archivo: así el dashboard abre sin internet,
    # en cualquier navegador o vista previa, y se puede mandar como un solo archivo.
    from plotly.offline import get_plotlyjs
    html = html.replace('<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>',
                        "<script>" + get_plotlyjs() + "</script>")
    Path(archivo).write_text(html, encoding="utf-8")
    i = VACAS.index(vaca_inicial)
    orden = sorted(zip(d["minutos"], VACAS), reverse=True)
    return {"vaca": vaca_inicial, "minutos": d["minutos"][i], "dias": d["dias"][i],
            "segunda": [orden[1][1], orden[1][0]],
            "pct_18_20": round(100 * sum(d["por_hora"][i][18:21]) / max(d["minutos"][i], 1), 1),
            "tendencia": d["tendencia"], "kpi": d["kpi"]}
