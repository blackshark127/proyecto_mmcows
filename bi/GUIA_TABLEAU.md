# Dashboard en Tableau Public: paso a paso

Objetivo: un tablero de **una sola pantalla** para el ganadero que responda "¿cómo va el grupo y qué vaca reviso?". Usa `vaca_dia.csv`, que genera `ejecutar_todo.py`: una fila por vaca y día, 150 filas.

Se compone de tres partes:
1. **Cuatro tarjetas KPI** con el resumen del grupo.
2. **Mapa de calor vaca × día** con los minutos sobre 39.2 °C. Es la versión de BI de la Fig. 4: ahí se ven las 10 vacas a la vez, no solo C09.
3. **Descanso por vaca**: horas echada por día con boxplot. Es la versión de BI de la Fig. 5.

Y se completa con filtros de vaca y fecha, tooltips personalizados y una acción de resaltado entre gráficas.

> Los nombres de menú van en español, y entre paréntesis en inglés por si tu Tableau está en ese idioma.

---

## 0. Instalar y conectar
1. Descarga **Tableau Public** (gratis) desde <https://public.tableau.com/app/discover> → *Crear/Download the app*. Crea tu cuenta, porque solo puedes guardar publicando en tu perfil.
2. Abre Tableau Public → **Conectar → Archivo de texto (Text file)** → elige `bi/vaca_dia.csv`.
3. En la vista de datos revisa los tipos. Tableau cambia `temp_promedio` por **Temp Promedio**, y así se llaman en las fórmulas.
   - `fecha` → **Fecha** (ícono de calendario).
   - `vaca`, `dia_completo` y `dia_atipico` → **Cadena (String)**.
   - Los demás → **Número decimal**.
4. Ve a **Hoja 1 (Sheet 1)**.

## 1. Campos calculados
Menú **Análisis → Crear campo calculado (Analysis → Create Calculated Field)**. Crea estos cuatro:

| Nombre | Fórmula | Formato |
|---|---|---|
| `KPI Temp promedio` | `SUM([Temp Promedio] * [Minutos Registrados]) / SUM([Minutos Registrados])` | Número, 2 decimales, sufijo " °C" |
| `KPI % sobre umbral` | `SUM([Minutos Sobre Umbral]) / SUM([Minutos Registrados])` | Porcentaje, 2 decimales |
| `KPI Horas echada` | `MEDIAN([Horas Echada])` | Número, 1 decimal, sufijo " h" |
| `KPI Días atípicos` | `SUM(IF [Dia Atipico] = "Sí" THEN 1 ELSE 0 END)` | Número entero |

La temperatura promedio se **pondera por minutos registrados**, porque el primer y el último día tienen menos lecturas. Un promedio simple de los promedios diarios les daría el mismo peso que a un día completo.

## 2. Tarjetas KPI (4 hojas)
Para cada KPI, en una hoja nueva:
1. Arrastra el campo calculado a **Marcas → Texto (Marks → Text)**.
2. Haz clic en **Texto → …** y escribe, por ejemplo:
   `Temperatura promedio del grupo` (tamaño 11, gris), Enter, `<AGG(KPI Temp promedio)>` (tamaño 28, negrita).
3. Nombra la hoja (por ejemplo "KPI Temp") y quítale el título.

**Valores que deben salir con todo el periodo** (sirven para comprobar que lo hiciste bien):

| KPI | Valor esperado |
|---|---|
| Temperatura promedio | **38.49 °C** |
| % de minutos ≥ 39.2 °C | **0.66 %** |
| Horas echada (mediana) | **13.2 h** |
| Días atípicos de descanso | **4** |

## 3. Mapa de calor: minutos sobre 39.2 °C por vaca y día
1. **Filas (Rows):** `Vaca`. **Columnas (Columns):** `Fecha`. Dale clic derecho → **Día exacto (Exact Date)** y luego cámbialo a **Discreto**. Formato `dd/mm`.
2. **Marcas:** tipo **Cuadrado (Square)**.
3. Arrastra `Minutos Sobre Umbral` a **Color** y a **Texto**.
4. Configura el color: **Editar colores → Naranja (secuencial)**, de blanco a naranja. Activa *Usar paso de color: 5* para que sean clases, como en el mapa del curso.
5. Ordena las vacas: clic derecho en `Vaca` → **Ordenar → Campo: Minutos Sobre Umbral, Suma, Descendente**. C09 queda arriba.
6. **Tooltip:** clic en **Información sobre herramientas (Tooltip)** y escribe:
   ```
   <Vaca> · <DAY(Fecha)>
   Minutos ≥ 39.2 °C: <SUM(Minutos Sobre Umbral)>
   Temperatura máxima: <SUM(Temp Maxima)> °C
   THI promedio del día: <SUM(Thi Promedio)>
   ```
7. Título: **"¿Cuándo se calienta cada vaca? Minutos sobre 39.2 °C"**.

Lo que debes ver: C09 arriba, con sus celdas más oscuras el 22/07 (122 min) y el 24/07 (114 min); el 27/07, el día más caluroso, C09 solo marca 10 min.

## 4. Descanso por vaca (versión BI de la Fig. 5)
1. **Columnas:** `Horas Echada`. **Filas:** `Vaca`.
2. Menú **Análisis → desmarca Agregar medidas (Aggregate Measures)**. Así sale un punto por vaca y día.
3. **Filtros:** arrastra `Dia Completo` y deja solo **Sí**.
4. **Marcas:** **Círculo**. Arrastra `Dia Atipico` a **Color**: **Sí = #E07B1A** (naranja) y **No = #A3A3A3** (gris). Es la misma regla de color del proyecto.
5. Pestaña **Análisis (Analytics)** → arrastra **Diagrama de caja (Box Plot)** a la vista → suéltalo en **Celda (Cell)**.
6. Ordena `Vaca` por **Horas Echada, Mediana, Descendente**.
7. **Tooltip:**
   ```
   <Vaca> · <DAY(Fecha)>
   Echada: <Horas Echada> h
   Desviación respecto a su propio promedio: <Desv Estandar Echada> desv. est.
   ¿Día atípico?: <Dia Atipico>
   ```
8. Título: **"Cada vaca tiene su propio normal de descanso"**.

## 5. Dashboard
1. Crea un **Nuevo dashboard**. Tamaño: **Fijo, 1200 × 800**.
2. Arriba pon un **Texto** con el título: "Monitoreo del grupo · MmCows, 10 vacas, 21 jul – 4 ago 2023".
3. Debajo, un **Contenedor horizontal** con las 4 hojas KPI.
4. Abajo, el mapa de calor a la izquierda (60 %) y el descanso por vaca a la derecha (40 %).
5. **Filtros:** en el mapa de calor, clic en ▾ → **Filtros → Vaca** y **Filtros → Fecha**. En cada filtro → **Aplicar a hojas de trabajo → Todas las que usan esta fuente de datos**. Para Vaca usa *Lista desplegable de varios valores* y para Fecha, *Rango de fechas*.
6. **Acción:** **Dashboard → Acciones → Agregar acción → Resaltar (Highlight)**.
   - Origen: mapa de calor.
   - Destino: descanso por vaca.
   - Ejecutar al: **Seleccionar**.
   - Campos: **Vaca**.

   Así, al hacer clic en una vaca del mapa se resaltan sus puntos de descanso.

## 6. Publicar
1. **Archivo → Guardar en Tableau Public como… (File → Save to Tableau Public As…)**. Ponle de nombre `Monitoreo collar MmCows`.
2. Se abre tu perfil en el navegador. Copia el enlace y pégalo en el README (tabla de visualizaciones) y en el documento del Avance 3.
3. Toma una captura del dashboard completo. Si puedes, toma otra con una vaca seleccionada y un tooltip abierto.

## Funciones de BI que demuestra este tablero
| Función | Dónde |
|---|---|
| KPIs / tarjetas de resumen | Las 4 tarjetas superiores |
| Filtros interactivos globales | Vaca y Fecha, aplicados a todas las hojas |
| Tooltips personalizados | Mapa de calor y descanso por vaca |
| Acción entre gráficas | Resaltar la vaca seleccionada en el mapa de calor |
| Analítica integrada | Diagrama de caja desde el panel de Análisis |
| Publicación web | Enlace público en Tableau Public |
