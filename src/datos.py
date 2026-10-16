"""Carga y limpieza de los datos de MmCows.

Este módulo concentra en un solo lugar las decisiones de limpieza que tomé en
el Avance 2. Las figuras del Avance 2 y las del Avance 3 lo usan, así que
todas parten de exactamente los mismos datos limpios.

Flujo:  cargar_crudos()  ->  limpiar()  ->  tablas_derivadas()
"""
import glob
import os
from pathlib import Path

import pandas as pd

VACAS = [f"C{i:02d}" for i in range(1, 11)]
UMBRAL_TEMP = 39.2                       # °C, referencia usada desde el Avance 1
TEMP_MINIMA_VIVA = 37.0                  # °C, por debajo es falla del sensor
CORTES_THI = [(0, 68, "sin estrés"), (68, 72, "leve"), (72, 80, "moderado"), (80, 200, "severo")]
MINUTOS_DIA = 1440


# ---------------------------------------------------------------------------
# Dónde están los datos
# ---------------------------------------------------------------------------
def ruta_datos(ruta=None) -> Path:
    """Devuelve la carpeta que contiene `main_data/`.

    Orden de búsqueda:
    1. el argumento `ruta`;
    2. la variable de entorno MMCOWS_DATA;
    3. `datos/mmcows/` dentro del proyecto (donde lo indica el README);
    4. cualquier carpeta "padre" del proyecto que tenga `main_data/`
       (así funciona también si el proyecto vive dentro de sensor_data).
    """
    candidatos = []
    if ruta:
        candidatos.append(Path(ruta))
    if os.environ.get("MMCOWS_DATA"):
        candidatos.append(Path(os.environ["MMCOWS_DATA"]))
    raiz = Path(__file__).resolve().parents[1]
    candidatos.append(raiz / "datos" / "mmcows")
    candidatos += list(raiz.parents)
    for c in candidatos:
        if (c / "main_data" / "cbt").is_dir():
            return c
    raise FileNotFoundError(
        "No encontré la carpeta main_data de MmCows. Descárgala como indica "
        "datos/README.md o define la variable de entorno MMCOWS_DATA."
    )


def a_hora_local(segundos: pd.Series) -> pd.Series:
    """Unix (UTC) -> hora local del experimento (CDT = UTC-5), según el README del dataset."""
    return (pd.to_datetime(segundos, unit="s", utc=True)
              .dt.tz_convert("Etc/GMT+5").dt.tz_localize(None))


def nivel_estres(thi: pd.Series) -> pd.Series:
    """THI -> nivel ordinal de estrés calórico (cortes 68 / 72 / 80)."""
    etiquetas = [c[2] for c in CORTES_THI]
    return pd.cut(thi, bins=[c[0] for c in CORTES_THI] + [CORTES_THI[-1][1]],
                  labels=etiquetas, right=False)


# ---------------------------------------------------------------------------
# 1. Carga
# ---------------------------------------------------------------------------
def cargar_crudos(ruta=None) -> dict:
    """Lee los CSV originales sin modificarlos (solo agrega la columna `cow`)."""
    D = ruta_datos(ruta) / "main_data"
    cbt = pd.concat([pd.read_csv(D / "cbt" / f"{v}.csv").assign(cow=v) for v in VACAS],
                    ignore_index=True)
    thi = pd.read_csv(D / "thi" / "average.csv")
    ankle = pd.concat([pd.read_csv(f).assign(cow=v) for v in VACAS
                       for f in sorted(glob.glob(str(D / "ankle" / v / "*.csv")))], ignore_index=True)
    # La ubicación usa T01–T10 para las mismas vacas C01–C10
    uwb = pd.concat([pd.read_csv(f).assign(cow=v) for v in VACAS
                     for f in sorted(glob.glob(str(D / "uwb" / v.replace("C", "T") / "*.csv")))],
                    ignore_index=True)
    return {"cbt": cbt, "thi": thi, "ankle": ankle, "uwb": uwb}


# ---------------------------------------------------------------------------
# 2. Limpieza
# ---------------------------------------------------------------------------
def limpiar(crudos: dict) -> tuple[dict, pd.DataFrame]:
    """Aplica las decisiones de limpieza del Avance 2.

    Devuelve (datos_limpios, reporte). El reporte documenta cada paso:
    qué problema encontré, cuántas filas afectó y qué decidí.
    """
    cbt, thi = crudos["cbt"].copy(), crudos["thi"].copy()
    ankle, uwb = crudos["ankle"].copy(), crudos["uwb"].copy()
    rep = []

    # a) Hora local
    for df in (cbt, thi, ankle, uwb):
        df["t"] = a_hora_local(df["timestamp"])
    rep.append(("Tiempo en formato Unix (UTC)", "todas", "Convertir a hora local CDT (UTC−5)"))

    # b) Lecturas imposibles de temperatura
    malas = cbt[cbt.temperature_C < TEMP_MINIMA_VIVA]
    cbt = cbt[cbt.temperature_C >= TEMP_MINIMA_VIVA]
    detalle = (f"{len(malas)} lecturas < 37 °C de {', '.join(malas.cow.unique())} "
               f"({malas.t.min():%d/%m %H:%M}–{malas.t.max():%H:%M}); mínima {malas.temperature_C.min()} °C")
    rep.append((detalle, len(malas), "Excluir: falla del sensor"))

    # c) Columna mal etiquetada en THI
    thi = thi.rename(columns={"temperature_F": "temperatura_aire_C"})
    rep.append(("Columna temperature_F con valores en °C (14–32)", 0, "Renombrar a temperatura_aire_C"))
    thi["nivel_estres"] = nivel_estres(thi.THI)

    # d) Días incompletos
    ankle["d"] = ankle.t.dt.date
    dias = sorted(ankle.d.unique())
    completos = [d for d in dias if ankle[ankle.d == d].groupby("cow").size().min() >= MINUTOS_DIA]
    incompletos = [d for d in dias if d not in completos]
    rep.append((f"Días incompletos: {', '.join(f'{d:%d/%m}' for d in incompletos)}",
                int(ankle.d.isin(incompletos).sum()),
                f"Para totales diarios usar solo los {len(completos)} días completos"))

    # e) Ubicación vacía
    n_vacias = int(uwb.coord_z_cm.isna().sum())
    pct = round(100 * uwb.coord_z_cm.isna().mean(), 1)
    uwb = uwb.dropna(subset=["coord_x_cm", "coord_y_cm", "coord_z_cm"])
    rep.append((f"Lecturas UWB vacías ({pct} %)", n_vacias, "Descartar esas filas"))

    reporte = pd.DataFrame(rep, columns=["problema", "filas_afectadas", "decision"])
    limpios = {"cbt": cbt.reset_index(drop=True), "thi": thi, "ankle": ankle,
               "uwb": uwb.reset_index(drop=True), "dias_completos": completos,
               "n_excluidas": int(len(malas)), "vacas_excluidas": malas.cow.unique().tolist()}
    return limpios, reporte


# ---------------------------------------------------------------------------
# 3. Tablas derivadas (las que usan las gráficas)
# ---------------------------------------------------------------------------
def tablas_derivadas(L: dict) -> dict:
    """Agrega los datos limpios a las resoluciones que usan las visualizaciones."""
    cbt, thi, ankle = L["cbt"], L["thi"], L["ankle"]

    # Por hora: temperatura de cada vaca y THI del corral
    temp_hora = (cbt.set_index("t").groupby("cow").temperature_C.resample("1h").mean()
                    .reset_index())
    thi_hora = thi.set_index("t").THI.resample("1h").mean().rename("THI").reset_index()
    thi_hora["nivel_estres"] = nivel_estres(thi_hora.THI)
    # Promedio móvil de 3 h (centrado) para suavizar el ruido minuto a minuto
    temp_hora["temp_suav"] = (temp_hora.groupby("cow").temperature_C
                              .transform(lambda s: s.rolling(3, center=True, min_periods=1).mean()))

    # Por vaca-día: horas echada (solo días completos) y su desviación respecto a la vaca
    ly = ankle[ankle.d.isin(L["dias_completos"])]
    echada = (ly.groupby(["cow", "d"]).lying.sum() / 60).rename("horas_echada").reset_index()
    echada["z"] = echada.groupby("cow").horas_echada.transform(lambda s: (s - s.mean()) / s.std())
    echada["dia_atipico"] = echada.z.abs() > 2

    cbt_d = cbt.assign(d=cbt.t.dt.date)
    temp_dia = cbt_d.groupby(["cow", "d"]).agg(
        temp_promedio=("temperature_C", "mean"),
        temp_maxima=("temperature_C", "max"),
        minutos_sobre_umbral=("temperature_C", lambda s: int((s >= UMBRAL_TEMP).sum())),
        minutos_registrados=("temperature_C", "size")).reset_index()
    thi_dia = (thi.assign(d=thi.t.dt.date).groupby("d").THI.agg(["mean", "max"])
                  .rename(columns={"mean": "thi_promedio", "max": "thi_maximo"}).reset_index())

    return {"temp_hora": temp_hora, "thi_hora": thi_hora, "echada": echada,
            "temp_dia": temp_dia, "thi_dia": thi_dia}


def cargar_todo(ruta=None):
    """Atajo: carga, limpia y deriva. Devuelve (limpios, reporte, tablas)."""
    L, rep = limpiar(cargar_crudos(ruta))
    return L, rep, tablas_derivadas(L)
