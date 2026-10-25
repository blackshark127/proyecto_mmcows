"""Reproduce todo el proyecto con un solo comando:

    python ejecutar_todo.py            (o)   python ejecutar_todo.py RUTA_A_MMCOWS

1. carga y limpia los datos            -> salidas/reporte_limpieza.csv
2. genera las 6 figuras del Avance 2    -> figuras/avance2/
3. genera las visualizaciones finales   -> figuras/avance3/
4. exporta las tablas para Tableau      -> bi/
5. genera el dashboard final            -> dashboard/index.html
6. guarda las cifras clave              -> salidas/cifras.json
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from datos import cargar_todo           # noqa: E402
import eda_avance2                      # noqa: E402
import avance3                          # noqa: E402
import dashboard                        # noqa: E402


def main(ruta=None):
    (RAIZ / "salidas").mkdir(exist_ok=True)
    (RAIZ / "figuras" / "avance3").mkdir(parents=True, exist_ok=True)

    print("1/6 Cargando y limpiando datos…")
    L, reporte, T = cargar_todo(ruta)
    reporte.to_csv(RAIZ / "salidas" / "reporte_limpieza.csv", index=False, encoding="utf-8-sig")

    print("2/6 Figuras del Avance 2…")
    cifras = {"avance2": eda_avance2.generar(L, RAIZ / "figuras" / "avance2")}

    print("3/6 Visualizaciones del Avance 3…")
    cifras["avance3_estatica"] = avance3.estatica_fig4(L, T, RAIZ / "figuras" / "avance3" / "fig4_estatica_final.png")
    avance3.interactiva_fig4(L, T, RAIZ / "figuras" / "avance3" / "fig4_interactiva.html")

    print("4/6 Tablas para Tableau…")
    cifras["bi"] = avance3.exportar_bi(L, T, RAIZ / "bi")

    print("5/6 Dashboard final…")
    (RAIZ / "dashboard").mkdir(exist_ok=True)
    cifras["dashboard"] = dashboard.generar(L, T, RAIZ / "dashboard" / "index.html")

    print("6/6 Cifras clave…")
    (RAIZ / "salidas" / "cifras.json").write_text(
        json.dumps(cifras, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("Listo.")
    return cifras


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
