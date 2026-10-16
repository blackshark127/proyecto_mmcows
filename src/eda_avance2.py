"""Las 6 visualizaciones exploratorias del Avance 2 (sin cambios de diseño).

Es el mismo código de `Avance2/graficas.py`, solo que ahora recibe los datos
ya limpios desde `datos.py` en lugar de cargarlos por su cuenta. Así la
limpieza vive en un solo lugar.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from estilo import GRAY, LGRAY, BLUE, ORANGE, INK, MUTED, aplicar_estilo, titulo
from datos import CORTES_THI


def generar(L: dict, carpeta) -> dict:
    """Genera fig1…fig6 en `carpeta` y devuelve las cifras clave (dict)."""
    aplicar_estilo()
    OUT = Path(carpeta); OUT.mkdir(parents=True, exist_ok=True)
    cbt = L["cbt"].copy(); thi = L["thi"].copy(); ly = L["ankle"]; uwb = L["uwb"]
    full_days = L["dias_completos"]
    lh = (ly[ly.d.isin(full_days)].groupby(["cow", "d"]).lying.sum() / 60).rename("h").reset_index()
    thi["d"] = thi.t.dt.date
    thi_d = thi.groupby("d").THI.mean()
    cats = CORTES_THI
    SHADE = ["#ffffff", "#efefef", "#dddddd", "#c6c6c6"]

    C = {}
    C["n_cbt"] = int(len(cbt)); C["n_art"] = L["n_excluidas"]; C["art_cow"] = L["vacas_excluidas"]
    C["cbt_mean"] = round(cbt.temperature_C.mean(), 2); C["cbt_median"] = round(cbt.temperature_C.median(), 2)
    C["cbt_p05"] = round(cbt.temperature_C.quantile(.05), 2); C["cbt_p95"] = round(cbt.temperature_C.quantile(.95), 2)
    C["pct_392"] = round(100 * (cbt.temperature_C >= 39.2).mean(), 2)
    C["min_392_by_cow"] = cbt[cbt.temperature_C >= 39.2].groupby("cow").size().sort_values(ascending=False).to_dict()
    C["thi_cat_pct"] = {lab: round(100 * ((thi.THI >= a) & (thi.THI < b)).mean(), 1) for a, b, lab in cats}
    C["thi_min"], C["thi_max"] = round(thi.THI.min(), 1), round(thi.THI.max(), 1)
    C["full_days"] = [str(full_days[0]), str(full_days[-1]), len(full_days)]

    # ======== Fig 1. Univariada: histograma de temperatura corporal ========
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    bins = np.arange(37.575, 39.626, 0.05)  # bordes a media centésima: evita huecos por redondeo a 0.01
    ax.hist(cbt.temperature_C, bins=bins, color=BLUE, edgecolor="white", linewidth=0.8)
    ax.axvline(39.2, color=ORANGE, ls="--", lw=1.6)
    ymax = ax.get_ylim()[1]
    ax.text(39.23, ymax * 0.82, f"39.2 °C\numbral de referencia\n{C['pct_392']} % de las lecturas",
            color=ORANGE, fontsize=8.5, va="top")
    ax.axvline(C["cbt_median"], color=INK, lw=1)
    ax.text(C["cbt_median"] - 0.03, ymax * 0.97, f"mediana {C['cbt_median']} °C", ha="right", va="top", fontsize=8.5, color=INK)
    ax.set_xlabel("Temperatura corporal central (°C)"); ax.set_ylabel("Número de lecturas (1 por minuto)")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{int(v):,}"))
    titulo(fig, "La temperatura corporal se concentra en un rango muy estrecho",
           f"10 vacas, 21 jul – 4 ago 2023 · n = {C['n_cbt']:,} lecturas · se excluyeron {C['n_art']} lecturas < 37 °C (falla del sensor de {C['art_cow'][0]})")
    fig.subplots_adjust(top=0.82, bottom=0.14, left=0.11, right=0.97)
    fig.savefig(OUT / "fig1_univariada.png"); plt.close(fig)

    # ======== Fig 2. Bivariada: THI diario vs horas echada ========
    x = lh.merge(thi_d.rename("thi").reset_index(), on="d")
    r = x[["h", "thi"]].corr().iloc[0, 1]
    b1, b0 = np.polyfit(x.thi, x.h, 1)
    C["r_lying_thi"] = round(r, 2); C["slope_lying_thi"] = round(b1, 2)
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.scatter(x.thi, x.h, s=26, color=BLUE, alpha=0.75, edgecolor="white", linewidth=0.6, zorder=3)
    xs = np.linspace(x.thi.min() - .3, x.thi.max() + .3, 50)
    ax.plot(xs, b0 + b1 * xs, color=INK, lw=1.6, zorder=4)
    ax.text(xs[-1], 17.45, f"tendencia: r = {r:.2f}\n≈ {abs(b1)*10:.1f} h menos echada\npor cada 10 puntos de THI",
            ha="right", va="top", fontsize=8.5, color=INK)
    low = x.nsmallest(2, "h")
    for _, rw in low.iterrows():
        ax.annotate(f"{rw.cow} · {pd.Timestamp(rw.d).strftime('%d/%m')}", (rw.thi, rw.h), xytext=(8, -2),
                    textcoords="offset points", fontsize=8, color=ORANGE)
        ax.scatter([rw.thi], [rw.h], s=34, color=ORANGE, zorder=5, edgecolor="white", linewidth=0.6)
    for a, b, lab in cats[:3]:
        if a > 0: ax.axvline(a, color=LGRAY, lw=0.8, zorder=1)
    ax.set_xlabel("THI promedio del día"); ax.set_ylabel("Horas echada en el día")
    titulo(fig, "En los días más calurosos las vacas pasan menos tiempo echadas",
           f"Cada punto es una vaca en un día completo · n = {len(x)} (10 vacas × {len(full_days)} días)")
    fig.subplots_adjust(top=0.82, bottom=0.13, left=0.09, right=0.97)
    fig.savefig(OUT / "fig2_bivariada.png"); plt.close(fig)

    # ======== Fig 3. Multivariada: perfil diario THI y temperatura por vaca ========
    cbt["hr"] = cbt.t.dt.hour; thi["hr"] = thi.t.dt.hour
    prof = cbt.groupby(["cow", "hr"]).temperature_C.mean().unstack(0)
    herd = cbt.groupby("hr").temperature_C.mean()
    thp = thi.groupby("hr").THI.agg(["mean", lambda s: s.quantile(.25), lambda s: s.quantile(.75)])
    thp.columns = ["m", "q1", "q3"]
    C["thi_peak_hr"] = int(thp.m.idxmax()); C["thi_peak"] = round(thp.m.max(), 1)
    C["cbt_peak_hr"] = int(herd.idxmax()); C["cbt_peak"] = round(herd.max(), 2)
    C["cbt_min_hr"] = int(herd.idxmin()); C["cbt_min"] = round(herd.min(), 2)
    # correlacion con desfase (datos por hora)
    ch = cbt.set_index("t").groupby("cow").temperature_C.resample("1h").mean().reset_index()
    thh = thi.set_index("t").THI.resample("1h").mean()
    lagr = {}
    for lag in range(0, 9):
        z = ch.merge(thh.shift(lag).rename("l").reset_index(), on="t").dropna()
        lagr[lag] = round(z[["temperature_C", "l"]].corr().iloc[0, 1], 2)
    C["lag_r"] = lagr
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 5.4), sharex=True, gridspec_kw={"height_ratios": [1, 1.4], "hspace": 0.12})
    a1.fill_between(thp.index, thp.q1, thp.q3, color=LGRAY, lw=0)
    a1.plot(thp.index, thp.m, color=INK, lw=2)
    a1.axvline(C["thi_peak_hr"], color=ORANGE, lw=1, ls=":")
    a1.text(C["thi_peak_hr"] + 0.2, thp.m.max() + 0.3, f"máximo {C['thi_peak_hr']}:00 h", color=ORANGE, fontsize=8.5)
    a1.set_ylabel("THI del corral"); a1.text(0.2, thp.q3.max() - 0.5, "línea: promedio · banda: 50 % central de los días", fontsize=7.5, color=MUTED)
    for c in prof.columns:
        a2.plot(prof.index, prof[c], color=GRAY, lw=0.8, alpha=0.8)
    a2.plot(herd.index, herd.values, color=BLUE, lw=2.6)
    a2.axvline(C["cbt_peak_hr"], color=ORANGE, lw=1, ls=":")
    a2.text(C["cbt_peak_hr"] + 0.2, prof.values.max() + 0.02, f"máximo {C['cbt_peak_hr']}:00 h\n(≈{C['cbt_peak_hr']-C['thi_peak_hr']} h después del THI)",
            color=ORANGE, fontsize=8.5, va="top")
    a2.text(23.3, herd.iloc[-1], "promedio\ndel hato", color=BLUE, fontsize=8, va="center")
    a2.text(23.3, prof.iloc[-1].min() - 0.05, "cada vaca", color=MUTED, fontsize=8, va="center")
    a2.set_ylabel("Temperatura corporal (°C)"); a2.set_xlabel("Hora del día (CDT)")
    a2.set_xticks(range(0, 24, 3)); a2.set_xticklabels([f"{h}:00" for h in range(0, 24, 3)]); a2.set_xlim(0, 23)
    titulo(fig, "La temperatura corporal sigue al calor del corral, pero con retraso",
           "Promedio por hora del día de los 14 días · arriba: THI · abajo: temperatura de cada vaca (gris) y del hato (azul)")
    fig.subplots_adjust(top=0.86, bottom=0.1, left=0.1, right=0.88)
    fig.savefig(OUT / "fig3_multivariada.png"); plt.close(fig)

    # ======== Fig 4. Temporal: serie de tiempo por hora con bandas THI ========
    top = max(C["min_392_by_cow"], key=C["min_392_by_cow"].get); C["top_cow"] = top
    hi = cbt[(cbt.cow == top) & (cbt.temperature_C >= 39.2)]
    C["top_hours"] = hi.t.dt.hour.value_counts().sort_index().to_dict()
    C["top_days"] = {str(k): int(v) for k, v in hi.t.dt.date.value_counts().sort_index().items()}
    C["top_share_18_20"] = round(100 * hi.t.dt.hour.between(18, 20).mean(), 1)
    C["top_share_first4"] = round(100 * (hi.t < pd.Timestamp("2023-07-25")).mean(), 1)
    sm = ch.set_index("t").groupby("cow").temperature_C.rolling(3, center=True, min_periods=1).mean().reset_index()
    oth = sm[sm.cow != top].groupby("t").temperature_C
    lo_, hi_, md_ = oth.min(), oth.max(), oth.median()
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    thh2 = thh.dropna()
    for t0, v in thh2.items():
        k = next(i for i, (a, b, _) in enumerate(cats) if a <= v < b)
        if k: ax.axvspan(t0, t0 + pd.Timedelta("1h"), color=SHADE[k], lw=0, zorder=0)
    ax.fill_between(lo_.index, lo_.values, hi_.values, color="#9aa7b8", alpha=0.45, lw=0, zorder=1)
    ax.plot(md_.index, md_.values, color="#555555", lw=0.9, zorder=2)
    g = sm[sm.cow == top]; ax.plot(g.t, g.temperature_C, color=ORANGE, lw=1.5, zorder=3)
    ax.axhline(39.2, color=BLUE, ls="--", lw=1.2, zorder=4)
    ax.set_ylim(37.85, 39.45)
    ax.text(ch.t.min(), 39.23, "umbral de referencia 39.2 °C", color=BLUE, fontsize=8, va="bottom")
    ax.text(1.0, 1.01, f"naranja: {top} · banda: rango de las otras 9 vacas · línea gris: su mediana",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=MUTED)
    ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=2))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d/%m"))
    ax.set_ylabel("Temperatura corporal (°C)")
    ax.legend(handles=[Patch(color=SHADE[i], label=cats[i][2]) for i in range(1, 4)], title="Estrés calórico (THI)",
              fontsize=7.5, title_fontsize=7.5, loc="lower left", ncol=3, frameon=False)
    titulo(fig, f"{top} se sale del grupo al anochecer, sobre todo los primeros días",
           "Promedio móvil de 3 horas · fondo: estrés calórico del corral por hora (cortes de THI 68 / 72 / 80)")
    fig.subplots_adjust(top=0.84, bottom=0.08, left=0.1, right=0.97)
    fig.savefig(OUT / "fig4_temporal.png"); plt.close(fig)

    # ======== Fig 5. Comparación de grupos: horas echada por vaca ========
    order = lh.groupby("cow").h.median().sort_values().index.tolist()
    herd_med = lh.h.median(); C["lying_herd_median"] = round(herd_med, 1)
    C["lying_by_cow"] = lh.groupby("cow").h.median().round(1).to_dict()
    lh["z"] = lh.groupby("cow").h.transform(lambda s: (s - s.mean()) / s.std())
    out = lh[lh.z.abs() > 2]; C["lying_outliers"] = [(r.cow, str(r.d), round(r.h, 1), round(r.z, 1)) for r in out.itertuples()]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    data = [lh[lh.cow == c].h.values for c in order]
    bp = ax.boxplot(data, orientation="horizontal", widths=0.55, patch_artist=True, showfliers=False,
                    medianprops=dict(color=BLUE, lw=2), boxprops=dict(facecolor="#e8eef7", edgecolor=BLUE, lw=1),
                    whiskerprops=dict(color=BLUE, lw=1), capprops=dict(color=BLUE, lw=1))
    rng = np.random.default_rng(1)
    for i, c in enumerate(order):
        g = lh[lh.cow == c]
        yy = i + 1 + rng.uniform(-0.18, 0.18, len(g))
        col = np.where(g.z.abs() > 2, ORANGE, GRAY)
        ax.scatter(g.h, yy, s=14, c=col, zorder=3, edgecolor="white", linewidth=0.4)
    ax.axvline(herd_med, color=INK, lw=1, ls=":")
    ax.text(herd_med + 0.1, len(order) + 0.45, f"mediana del hato {herd_med:.1f} h", fontsize=8.5, color=INK)
    ax.set_yticks(range(1, len(order) + 1)); ax.set_yticklabels(order)
    ax.set_xlabel("Horas echada por día"); ax.set_ylim(0.4, len(order) + 0.8)
    for r_ in out.itertuples():
        i = order.index(r_.cow) + 1
        ax.annotate(f"{pd.Timestamp(r_.d).strftime('%d/%m')}", (r_.h, i), xytext=(0, -11), textcoords="offset points",
                    ha="center", fontsize=7, color=ORANGE)
    titulo(fig, "Cada vaca tiene su propio \"normal\" de descanso",
           f"Horas echada por día · {len(full_days)} días completos · naranja: días a más de 2 desv. estándar de su propio promedio")
    fig.subplots_adjust(top=0.84, bottom=0.12, left=0.08, right=0.97)
    fig.savefig(OUT / "fig5_grupos.png"); plt.close(fig)

    # ======== Fig 6. Collar: altura del cuello (UWB z) según postura ========
    u = uwb.copy(); u["m"] = u.t.dt.floor("min")
    um = u.groupby(["cow", "m"]).coord_z_cm.median().reset_index()
    xz = um.merge(ly.rename(columns={"t": "m"})[["cow", "m", "lying"]], on=["cow", "m"])
    acc = {thr: round(100 * ((xz.coord_z_cm < thr).astype(int) == xz.lying).mean(), 1) for thr in range(80, 131, 5)}
    best = max(acc, key=acc.get); C["z_acc"] = acc; C["z_best"] = [best, acc[best]]; C["z_n"] = int(len(xz))
    C["z_med"] = xz.groupby("lying").coord_z_cm.median().round(0).to_dict()
    
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    bz = np.arange(40, 201, 3)
    ax.hist(xz[xz.lying == 0].coord_z_cm, bins=bz, color=GRAY, alpha=0.75, label="de pie (sensor de la pata)")
    ax.hist(xz[xz.lying == 1].coord_z_cm, bins=bz, histtype="step", color=BLUE, lw=2, label="echada (sensor de la pata)")
    ax.axvline(best, color=ORANGE, ls="--", lw=1.6)
    ax.text(best + 2, ax.get_ylim()[1] * 0.95, f"corte simple en {best} cm:\ncoincide con la pata\nen el {acc[best]} % de los minutos",
            color=ORANGE, fontsize=8.5, va="top")
    ax.set_xlabel("Altura del collar sobre el piso (cm, mediana por minuto)"); ax.set_ylabel("Minutos")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{int(v):,}"))
    ax.legend(frameon=False, fontsize=8.5, loc="center right")
    titulo(fig, "¿El collar puede saber si la vaca está echada?",
           f"Altura del collar (UWB) vs. postura registrada por el sensor de la pata · n = {C['z_n']:,} minutos")
    fig.subplots_adjust(top=0.82, bottom=0.14, left=0.11, right=0.97)
    fig.savefig(OUT / "fig6_collar.png"); plt.close(fig)

    return C
