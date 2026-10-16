# Datos: cómo obtener MmCows

Los datos **no se incluyen en el repositorio** por dos razones: la licencia de MmCows es académica y no comercial (se cita, no se redistribuye), y el dataset completo pesa unos 18 GB.

## Pasos

1. Entra a <https://huggingface.co/datasets/neis-lab/mmcows> y descarga `sensor_data`. Solo se necesitan estas cuatro carpetas de `main_data`, unos 44 MB:
   - `main_data/cbt/`
   - `main_data/thi/`
   - `main_data/ankle/`
   - `main_data/uwb/`
2. Colócalas así dentro del proyecto:

```
datos/
└── mmcows/
    └── main_data/
        ├── cbt/      C01.csv … C10.csv
        ├── thi/      average.csv
        ├── ankle/    C01/ … C10/   (un CSV por día)
        └── uwb/      T01/ … T10/   (un CSV por día)
```

3. Corre `py ejecutar_todo.py`.

Si prefieres dejar los datos en otro lugar, define la variable de entorno `MMCOWS_DATA` con la carpeta que contiene `main_data`, o pásala como argumento: `py ejecutar_todo.py D:/mis_datos/sensor_data`.

## Nota sobre los identificadores

La misma vaca aparece como **C01–C10** en los archivos de temperatura y de la pata, y como **T01–T10** en los de ubicación (UWB). El código los une por número: `T04` es `C04`.

## Formato original de cada archivo

| Archivo | Columnas | Unidades |
|---|---|---|
| `cbt/Cxx.csv` | `timestamp`, `temperature_C` | Unix (s), °C |
| `thi/average.csv` | `timestamp`, `temperature_F`*, `humidity_per`, `THI` | Unix (s), °C*, %, adimensional |
| `ankle/Cxx/Cxx_MMDD.csv` | `timestamp`, `datetime`, `lying` | Unix (s), texto, 0/1 |
| `uwb/Txx/Txx_MMDD.csv` | `timestamp`, `coord_x_cm`, `coord_y_cm`, `coord_z_cm` | Unix (s), cm |

\* La columna se llama `temperature_F`, pero sus valores (14 a 32) están en grados Celsius. El código la renombra a `temperatura_aire_C`.

