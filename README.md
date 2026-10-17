# Monitoreo de ganado con collar: visualización de datos de MmCows

Proyecto de la materia **Visualización de Datos 2026B** (Maestría Profesionalizante en Inteligencia Artificial, TecNM / Instituto Tecnológico de Aguascalientes).
Autor: **Rafael Said De la Paz Coronado** · Profesor: Dr. Ricardo Emmanuel Reyes Acosta.

## Pregunta del proyecto

> ¿Cómo responden la temperatura corporal y el tiempo echada de cada vaca al estrés calórico del corral, qué tan distinto es el patrón normal de cada una, y puede un collar (sin sensor en la pata) capturar esas señales?

**Audiencia:** el ganadero (vista de alerta: ¿qué animal reviso?) y el veterinario (vista de detalle).

## Datos

- **Fuente:** MmCows, un dataset multimodal de 16 vacas lecheras durante 14 días en verano (21 jul – 4 ago 2023), publicado por Vu et al. (2024) en NeurIPS.
  Descarga: <https://huggingface.co/datasets/neis-lab/mmcows>
- **Licencia:** uso académico citando a los autores, no comercial. Por eso **los datos no están en este repositorio**; ver [`datos/README.md`](datos/README.md) para descargarlos.
- **Qué se usa:** solo cuatro carpetas de `main_data` (unos 44 MB de los 18 GB):

| Carpeta | Variable | Frecuencia |
|---|---|---|
| `cbt/` | Temperatura corporal central (°C), C01–C10 | 1 por minuto |
| `thi/average.csv` | Índice temperatura-humedad (THI) del corral | 1 por minuto |
| `ankle/` | Echada (1) / de pie (0), sensor de la pata | 1 por minuto |
| `uwb/` | Posición 3D del collar (x, y, z en cm), T01–T10 | cada 15 s |

## Cómo reproducirlo

```bash
py -m pip install -r requirements.txt
py ejecutar_todo.py                 # busca los datos en datos/mmcows/
py ejecutar_todo.py C:/ruta/a/mmcows # o indicando la ruta
```

La ejecución regenera: las figuras de `figuras/`, las tablas de `bi/` y las cifras de `salidas/`.
Para seguir el análisis paso a paso con explicaciones, abre **`notebooks/Proyecto_MmCows.ipynb`** (Jupyter, VS Code o Google Colab).

## Estructura

```
proyecto_mmcows/
├── README.md                ← este archivo
├── requirements.txt         ← librerías y versiones
├── ejecutar_todo.py         ← reproduce todo con un comando
├── datos/README.md          ← cómo descargar MmCows (los datos no se suben)
├── src/
│   ├── datos.py             ← carga, limpieza y tablas derivadas (un solo lugar)
│   ├── estilo.py            ← paleta y estilo común
│   ├── eda_avance2.py       ← las 6 figuras exploratorias del Avance 2
│   └── avance3.py           ← versión estática final, interactiva y exportación a BI
├── notebooks/
│   └── Proyecto_MmCows.ipynb  ← carga → limpieza → EDA → visualizaciones finales
├── figuras/
│   ├── avance2/             ← fig1…fig6 (PNG)
│   └── avance3/             ← fig4_estatica_final.png, fig4_interactiva.html
├── bi/
│   ├── vaca_dia.csv         ← tabla para Tableau (una fila por vaca y día)
│   ├── vaca_hora.csv        ← tabla para Tableau (una fila por vaca y hora)
│   └── GUIA_TABLEAU.md      ← cómo se construyó el dashboard
└── salidas/
    ├── reporte_limpieza.csv ← cada problema de calidad y la decisión tomada
    └── cifras.json          ← todas las cifras citadas en los documentos
```

## Limpieza aplicada

| Problema | Filas | Decisión |
|---|---|---|
| Tiempos en Unix (UTC) | todas | Convertir a hora local CDT (UTC−5), según el README del dataset |
| 10 lecturas < 37 °C de C09 (25/07, 7:20–7:29; mínima 21.9 °C) | 10 | Excluir: una vaca viva no puede tener esa temperatura (falla del sensor) |
| Columna `temperature_F` del THI con valores en °C (14–32) | 0 | Renombrar a `temperatura_aire_C` |
| Primer y último día incompletos (21/07 desde 12:30, 04/08 hasta 7:00) | 10,720 | Para totales diarios, usar solo los 13 días completos |
| 4.9 % de lecturas UWB vacías | 39,024 | Descartar esas filas |

## Visualizaciones

| Archivo | Herramienta | Qué responde |
|---|---|---|
| `figuras/avance2/fig1…fig6` | matplotlib (estática) | EDA del Avance 2: distribución, relación con el THI, ciclo diario, serie de tiempo, descanso por vaca y altura del collar |
| `figuras/avance3/fig4_estatica_final.png` | matplotlib (estática) | ¿Cuándo se sale C09 del grupo? Versión final con anotaciones |
| `figuras/avance3/fig4_interactiva.html` | Plotly (interactiva) | La misma pregunta para cualquier vaca: selector, detalle al pasar el cursor y zoom |
| Dashboard en Tableau Public | Tableau (BI) | Resumen del grupo: KPIs, calor por vaca y día, y descanso por vaca con filtros. Libro local: [`bi/Monitoreo_MmCows_final.twbx`](bi/Monitoreo_MmCows_final.twbx). Publicación en Tableau Public pendiente. |

## Referencia

Vu, H., Prabhune, O. C., Raskar, U., Panditharatne, D., Chung, H., Choi, C., & Kim, Y. (2024). MmCows: A multimodal dataset for dairy cattle monitoring. *Advances in Neural Information Processing Systems, 37*, 59451–59467.

## Estado y seguimiento

Repositorio: https://github.com/blackshark127/proyecto_mmcows

Link para acceder a las visualizaciones de tableau

### Entorno Windows

Se usa  py. para que la ejecución completa terminó correctamente con pandas, numpy, matplotlib y plotly. La instalación completa de requirements.txt en Python 3.15 encontró un error de compilación de PyYAML, relacionado con las dependencias del notebook. Para regenerar las figuras puede instalarse el conjunto básico con:

    py -m pip install pandas numpy matplotlib plotly
    py ejecutar_todo.py C:/ruta/a/sensor_data

Los CSV de bi son agregaciones derivadas para Tableau. Los archivos originales de sensor_data no se incluyen.

