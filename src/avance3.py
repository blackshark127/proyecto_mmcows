"""Avance 3: la Fig. 4 del Avance 2 llevada a versión estática final e interactiva,
y la exportación de tablas para el componente de BI (Tableau Public).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch

from estilo import BLUE, ORANGE, INK, MUTED, ESTRES, aplicar_estilo, titulo
from datos import UMBRAL_TEMP, VACAS

BANDA = "#c9d3df"        # rango de las otras vacas (contexto, azul grisáceo muy claro)
MEDIANA = "#6b6b6b"      # mediana de las otras vacas


def _grupo_vs_vaca(temp_hora: pd.DataFrame, vaca: str) -> pd.DataFrame:
    """Para cada hora: temperatura de `vaca` y rango/mediana de las otras 9."""
    otras = temp_hora[temp_hora.cow != vaca].groupby("t").temp_suav
    g = pd.DataFrame({"min": otras.min(), "max": otras.max(), "mediana": otras.median()})
    v = temp_hora[temp_hora.cow == vaca].set_index("t").temp_suav.rename("vaca")
    return g.join(v, how="inner").reset_index()


# ---------------------------------------------------------------------------
# 1. Versión estática final (matplotlib)
# ---------------------------------------------------------------------------
def estatica_fig4(L: dict, T: dict, archivo, vaca: str = "C09") -> dict:
    """Fig. 4 mejorada. Cambios respecto al Avance 2:
    - el estrés calórico sale del fondo y pasa a una franja propia abajo
      (antes las bandas grises competían con la banda de las vacas);
    - anotaciones que dicen el hallazgo en la gráfica (cuándo y cuánto);
    - etiquetas directas al final de las líneas en lugar de una leyenda arriba;
    - el umbral se rotula a la derecha, donde termina la lectura.
    """
    aplicar_estilo()
    cbt = L["cbt"]
    sobre = cbt[(cbt.cow == vaca) & (cbt.temperature_C >= UMBRAL_TEMP)]
    total = len(sobre)
    pct_noche = round(100 * sobre.t.dt.hour.between(18, 20).mean(), 1)
    pct_inicio = round(100 * (sobre.t < pd.Timestamp("2023-07-25")).mean(), 1)
    dia_caluroso = T["thi_dia"].sort_values("thi_promedio").iloc[-1]
    min_caluroso = int((sobre.t.dt.date == dia_caluroso.d).sum())

    g = _grupo_vs_vaca(T["temp_hora"], vaca)
    th = T["thi_hora"].dropna(subset=["THI"])

    fig = plt.figure(figsize=(7.4, 4.9))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 0.09], hspace=0.08)
    ax = fig.add_subplot(gs[0]); ax2 = fig.add_subplot(gs[1], sharex=ax)

    # Periodo de los primeros 4 días: contexto muy suave en naranja
    ini, fin = g.t.min(), pd.Timestamp("2023-07-25")
    ax.axvspan(ini, fin, color=ORANGE, alpha=0.07, lw=0, zorder=0)
    ax.text(ini + pd.Timedelta("3h"), 39.47, f"Primeros 4 días:\n{pct_inicio:.0f} % de sus {total} min\nsobre el umbral", fontsize=8, color=ORANGE, va="top")

    ax.fill_between(g.t, g["min"], g["max"], color=BANDA, lw=0, zorder=1)
    ax.plot(g.t, g.mediana, color=MEDIANA, lw=0.9, zorder=2)
    ax.plot(g.t, g.vaca, color=ORANGE, lw=1.7, zorder=3)
    ax.axhline(UMBRAL_TEMP, color=BLUE, ls="--", lw=1.1, zorder=4)

    # Pico típico al anochecer (el máximo de los primeros días)
    pico = g[g.t < fin].nlargest(1, "vaca").iloc[0]
    ax.annotate(f"{pico.t:%d/%m %H:%M} h · {pico.vaca:.2f} °C\n{pct_noche:.0f} % de sus minutos altos\nocurren entre 18:00 y 20:00",
                xy=(pico.t, pico.vaca), xytext=(pd.Timestamp("2023-07-25 20:00"), 39.36),
                fontsize=8, color=INK, va="center", ha="left",
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.7))

    # Día más caluroso: casi no se sale
    x_cal = pd.Timestamp(dia_caluroso.d) + pd.Timedelta("12h")
    ax.annotate(f"{pd.Timestamp(dia_caluroso.d):%d/%m}: el día más caluroso\n(THI prom. {dia_caluroso.thi_promedio:.1f})\n"
                f"solo {min_caluroso} min sobre el umbral",
                xy=(x_cal, 38.15), xytext=(x_cal, 37.9), fontsize=8, color=INK, ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85))

    # Etiquetas directas a la derecha
    x_fin = g.t.max() + pd.Timedelta("4h")
    ax.text(x_fin, UMBRAL_TEMP, f"{UMBRAL_TEMP} °C\nreferencia", color=BLUE, fontsize=8, va="center")
    ax.text(x_fin, g.vaca.iloc[-8:].mean() - 0.05, vaca, color=ORANGE, fontsize=9, fontweight="bold", va="center")
    ax.text(x_fin, g.mediana.iloc[-8:].mean() + 0.17, "otras 9 vacas\nbanda: rango\nlínea: mediana",
            color=MEDIANA, fontsize=7.5, va="center")

    ax.set_ylim(37.85, 39.5)
    ax.set_ylabel("Temperatura corporal (°C)")
    ax.tick_params(axis="x", labelbottom=False)
    ax.set_xlim(g.t.min(), g.t.max())

    # Franja de estrés calórico (ordinal, escala secuencial de un tono)
    for _, r in th.iterrows():
        ax2.axvspan(r.t, r.t + pd.Timedelta("1h"), color=ESTRES[str(r.nivel_estres)], lw=0)
    ax2.set_yticks([]); ax2.spines["left"].set_visible(False)
    ax2.set_ylabel("THI", rotation=0, ha="right", va="center", fontsize=8, color=MUTED)
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax2.legend(handles=[Patch(color=c, label=k) for k, c in ESTRES.items()],
               title="Estrés calórico del corral (por hora)", ncol=4, fontsize=7.5, title_fontsize=7.5,
               frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.9))

    titulo(fig, f"{vaca} rebasa el umbral al anochecer de sus primeros días",
           "Temperatura corporal, promedio móvil de 3 h · 10 vacas, 21 jul – 4 ago 2023 · datos: MmCows (Vu et al., 2024)")
    fig.subplots_adjust(top=0.86, bottom=0.2, left=0.09, right=0.86)
    fig.savefig(archivo); plt.close(fig)
    return {"vaca": vaca, "min_sobre": total, "pct_18_20": pct_noche, "pct_primeros4": pct_inicio,
            "dia_caluroso": str(dia_caluroso.d), "thi_dia_caluroso": round(dia_caluroso.thi_promedio, 1),
            "min_dia_caluroso": min_caluroso, "pico": [f"{pico.t:%d/%m %H:%M}", round(pico.vaca, 2)]}


# ---------------------------------------------------------------------------
# 2. Versión interactiva (Plotly)
# ---------------------------------------------------------------------------
def interactiva_fig4(L: dict, T: dict, archivo, vaca_inicial: str = "C09"):
    """La misma Fig. 4, pero el usuario elige qué vaca comparar contra el grupo.

    Interacciones:
    - menú "Vaca a revisar" (selección dinámica): cambia la vaca resaltada;
    - hover con detalle que no cabe en la estática: diferencia contra la
      mediana del grupo y THI/nivel de estrés de esa hora;
    - zoom con botones (1 día, 3 días, todo) y barra de rango.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    cbt = L["cbt"]
    minutos = cbt[cbt.temperature_C >= UMBRAL_TEMP].groupby("cow").size().reindex(VACAS, fill_value=0)
    th = T["thi_hora"].dropna(subset=["THI"]).copy()
    th["nivel_estres"] = th.nivel_estres.astype(str)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.04)
    trazas_por_vaca = 4
    for vaca in VACAS:
        g = _grupo_vs_vaca(T["temp_hora"], vaca).merge(th[["t", "THI", "nivel_estres"]], on="t", how="left")
        g["dif"] = g.vaca - g.mediana
        vis = vaca == vaca_inicial
        fig.add_trace(go.Scatter(x=g.t, y=g["min"], mode="lines", line=dict(width=0), hoverinfo="skip",
                                 showlegend=False, visible=vis), row=1, col=1)
        fig.add_trace(go.Scatter(x=g.t, y=g["max"], mode="lines", line=dict(width=0), fill="tonexty",
                                 fillcolor=BANDA, hoverinfo="skip", name="rango de las otras 9",
                                 visible=vis), row=1, col=1)
        fig.add_trace(go.Scatter(x=g.t, y=g.mediana, mode="lines", line=dict(color=MEDIANA, width=1),
                                 name="mediana de las otras 9", visible=vis,
                                 hovertemplate="Mediana de las otras 9: %{y:.2f} °C<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=g.t, y=g.vaca, mode="lines", line=dict(color=ORANGE, width=2), name=vaca, visible=vis,
            customdata=np.stack([g.dif, g.THI, g.nivel_estres.fillna("—")], axis=-1),
            hovertemplate=(f"<b>{vaca}</b>: %{{y:.2f}} °C<br>"
                           "Diferencia vs. grupo: %{customdata[0]:+.2f} °C<br>"
                           "THI del corral: %{customdata[1]:.1f} (%{customdata[2]})<extra></extra>")),
            row=1, col=1)

    # Franja de THI abajo (barras por hora coloreadas por nivel de estrés)
    for nivel, color in ESTRES.items():
        s = th[th.nivel_estres == nivel]
        fig.add_trace(go.Bar(x=s.t, y=[1] * len(s), marker_color=color, marker_line_width=0, width=3.6e6,
                             name=f"estrés: {nivel}", customdata=s.THI, showlegend=False,
                             hovertemplate=f"THI %{{customdata:.1f}} · {nivel}<extra></extra>"), row=2, col=1)
    n_vacas = len(VACAS) * trazas_por_vaca
    n_thi = len(ESTRES)

    botones = []
    for i, vaca in enumerate(VACAS):
        vis = [False] * n_vacas + [True] * n_thi
        for k in range(trazas_por_vaca):
            vis[i * trazas_por_vaca + k] = True
        botones.append(dict(label=f"{vaca}  ({minutos[vaca]} min ≥ {UMBRAL_TEMP} °C)", method="update",
                            args=[{"visible": vis},
                                  {"title.text": f"<b>{vaca} contra las otras 9 vacas</b><br><sup>Temperatura corporal, "
                                                 "promedio móvil de 3 h · elige otra vaca en el menú · pasa el cursor "
                                                 "para ver el detalle</sup>"}]))
    fig.update_layout(
        updatemenus=[dict(buttons=botones, direction="down", x=0.0, xanchor="left", y=1.13, yanchor="top",
                          active=VACAS.index(vaca_inicial), bgcolor="white", font=dict(size=12))],
        annotations=[dict(text="Vaca a revisar:", x=0.0, xref="paper", y=1.17, yref="paper",
                          showarrow=False, xanchor="left", font=dict(size=12, color=MUTED))],
        title=dict(text=f"<b>{vaca_inicial} contra las otras 9 vacas</b><br><sup>Temperatura corporal, promedio móvil "
                        "de 3 h · elige otra vaca en el menú · pasa el cursor para ver el detalle</sup>",
                   x=0.01, y=0.97),
        template="plotly_white", font=dict(family="Arial", size=12), hovermode="x unified",
        bargap=0, barmode="overlay", height=620, width=1100,
        margin=dict(l=70, r=30, t=130, b=95),
        legend=dict(orientation="h", y=1.02, x=0.3, yanchor="bottom", font=dict(size=11)),
    )
    fig.add_hline(y=UMBRAL_TEMP, line=dict(color=BLUE, dash="dash", width=1.2), row=1, col=1,
                  annotation_text=f"{UMBRAL_TEMP} °C referencia", annotation_position="top left",
                  annotation_font=dict(color=BLUE, size=11))
    fig.update_yaxes(title_text="Temperatura (°C)", range=[37.85, 39.5], row=1, col=1, gridcolor="#eeeeee")
    fig.update_yaxes(visible=False, row=2, col=1)
    fig.update_xaxes(row=2, col=1, hoverformat="%d/%m/%Y %H:%M", tickformatstops=[
        dict(dtickrange=[None, 86400000], value="%d/%m<br>%H:%M"),
        dict(dtickrange=[86400000, None], value="%d/%m")])
    fig.update_xaxes(row=1, col=1, hoverformat="%d/%m/%Y %H:%M")
    fig.add_annotation(text="Franja inferior: estrés calórico del corral por hora (más oscuro = más estrés: "
                            "sin estrés, leve, moderado, severo)", xref="paper", yref="paper", x=0, y=-0.17,
                       showarrow=False, xanchor="left", font=dict(size=11, color=MUTED))
    fig.update_xaxes(row=1, col=1, rangeselector=dict(
        x=1, xanchor="right", y=1.08, buttons=[dict(count=1, label="1 día", step="day", stepmode="backward"),
                                              dict(count=3, label="3 días", step="day", stepmode="backward"),
                                              dict(step="all", label="Todo")]))
    fig.write_html(archivo, include_plotlyjs="cdn")
    return fig


# ---------------------------------------------------------------------------
# 3. Tablas para Tableau Public (BI)
# ---------------------------------------------------------------------------
def exportar_bi(L: dict, T: dict, carpeta) -> dict:
    """Escribe dos CSV "planos" listos para arrastrar en Tableau:
    - vaca_dia.csv  : una fila por vaca y día (para KPIs, boxplot y filtros);
    - vaca_hora.csv : una fila por vaca y hora (para la serie de tiempo).
    """
    carpeta = Path(carpeta); carpeta.mkdir(parents=True, exist_ok=True)
    d = (T["temp_dia"].merge(T["thi_dia"], on="d", how="left")
                      .merge(T["echada"][["cow", "d", "horas_echada", "z", "dia_atipico"]], on=["cow", "d"], how="left"))
    d["dia_completo"] = d.d.isin(L["dias_completos"]).map({True: "Sí", False: "No"})
    d["dia_atipico"] = d.dia_atipico.map({True: "Sí", False: "No"}).fillna("Sin dato")
    d = d.rename(columns={"cow": "vaca", "d": "fecha", "z": "desv_estandar_echada"})
    d = d[["vaca", "fecha", "dia_completo", "horas_echada", "desv_estandar_echada", "dia_atipico",
           "temp_promedio", "temp_maxima", "minutos_sobre_umbral", "minutos_registrados",
           "thi_promedio", "thi_maximo"]].round(3)
    d.to_csv(carpeta / "vaca_dia.csv", index=False, encoding="utf-8-sig")

    h = T["temp_hora"].merge(T["thi_hora"], on="t", how="left")
    h = h.rename(columns={"cow": "vaca", "t": "fecha_hora", "temperature_C": "temp_promedio_hora",
                          "temp_suav": "temp_movil_3h"})
    h["nivel_estres"] = h.nivel_estres.astype(str).replace("nan", "")
    h.round(3).to_csv(carpeta / "vaca_hora.csv", index=False, encoding="utf-8-sig")

    cbt = L["cbt"]
    comp = d[d.dia_completo == "Sí"]
    kpi = {"temp_mediana": round(cbt.temperature_C.median(), 2),
           "pct_minutos_sobre_umbral": round(100 * (cbt.temperature_C >= UMBRAL_TEMP).mean(), 2),
           "horas_echada_mediana": round(comp.horas_echada.median(), 1),
           "dias_atipicos": int((comp.dia_atipico == "Sí").sum()),
           "filas_vaca_dia": len(d), "filas_vaca_hora": len(h)}
    return kpi
