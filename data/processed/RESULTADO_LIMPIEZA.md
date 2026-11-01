# Datos procesados: resultado de la inspección y la limpieza

Este documento resume la corrida de `notebooks/inspeccion_y_limpieza.ipynb` del **1 de noviembre de 2026**: qué datos recibió, qué problemas se encontraron en los archivos originales, qué se hizo con cada uno y cómo quedaron los archivos de esta carpeta.

El detalle de cada problema de formato está en `data/README.md`. El análisis de los datos procesados está en `notebooks/exploracion_inicial.ipynb`.

---

## 1. Qué recibió el notebook

12 zips anuales del dataset [Subte - viajes por molinete](https://data.buenosaires.gob.ar/dataset/subte-viajes-molinetes) (SBASE, GCBA), guardados en Google Drive. Su tamaño y su SHA-256 están en `data/MANIFEST.md`.

| Año | Archivos CSV | Filas originales | Tamaño descomprimido |
| :--- | ---: | ---: | ---: |
| 2015 | 1 | 10.958.582 | 1.087 MB |
| 2016 | 1 | 11.542.322 | 1.077 MB |
| 2017 | 1 | 11.938.476 | 1.243 MB |
| 2018 | 1 | 12.136.454 | 1.180 MB |
| 2019 | 1 | 12.662.343 | 1.239 MB |
| 2020 | 1 | 5.781.006 | 465 MB |
| 2021 | 1 | 8.071.680 | 689 MB |
| 2022 | 24 (uno por mes, líneas ABC y DEH) | 12.136.381 | 1.034 MB |
| 2023 | 24 | 12.047.696 | 1.015 MB |
| 2024 | 24 | 11.440.440 | 952 MB |
| 2025 | 26 (suma PM en junio y julio) | 13.279.071 | 1.101 MB |
| 2026 | 21 (enero a agosto; suma PM en 5 meses) | 9.951.035 | 796 MB |
| **Total** | **126** | **131.945.486** | **≈ 11,9 GB** |

Cada fila original es la cantidad de personas que pasaron por **un molinete** en **un tramo de 15 minutos**.

El zip de 2015 trae además 9 zips internos con copias de otros años; no se usaron, porque cada año se toma de su propio zip.

---

## 2. Problemas encontrados en los archivos originales

La inspección recorrió los 126 CSV completos sin modificarlos (6 minutos). Sus resultados coinciden exactamente con una primera inspección hecha el 17 de octubre de 2026.

| Problema | Dónde | Qué se hizo |
| :--- | :--- | :--- |
| **Separador distinto** (`,` o `;`) | `,` hasta 2020; `;` desde 2021 | Se detecta en cada archivo. |
| **Nombres de columnas distintos** | `PAX_FREQ` (2016-2017), `pax_TOTAL` (2020-2026), `total` (resto) | Se renombran a `pax_franq` y `total`. |
| **Columnas de más** | `V1`, `ID_ESTACION`, `periodo`, `origen` y 4 columnas auxiliares en junio y septiembre de 2022 | Se ignoran. |
| **Fechas en formatos mezclados dentro del mismo archivo** | 2020 (día/mes y mes/día), 2021 (día/mes e ISO invertida), agosto de 2025 (día/mes y mes/día) | Se elige la lectura correcta: en 2020 y 2021, la más cercana al día siguiente de la fila anterior (el archivo está ordenado); desde 2022, la que cae en el mes del nombre del archivo. |
| **Filas desordenadas** | 2016, 2017 y todos los archivos mensuales (2022-2026) | Por eso desde 2022 la fecha se resuelve con el mes del archivo y no con el orden. |
| **Codificación mixta** (UTF-8 y latin-1) | 2016 (116.667 líneas), 2017 (117.169), 2022 (500.289), 2024 (50.098), 2025 (30.537) | Cada línea se lee como UTF-8 y, si falla, como latin-1. |
| **Líneas enteras entre comillas**, a veces con `;;;;;;;;;` al final | Casi todos los archivos de 2022 a 2026 | Se sacan las comillas y lo que sobra. |
| **Hora sin segundos** (`12:15`) | Algunos meses de 2025 y 2026 | No afecta: solo se usa la hora. |
| **La línea escrita de tres formas** (`A`, `LINEA_A`, `LineaA`) | 2015 a 2017 | Se unifica como `LineaA`. |
| **Nombres de estaciones dañados** (`SAENZ PEÃ±A`, `SAENZ PE�A`, `SAENZ PE¤A`, `AGÃ¼ERO`, `AG�ERO`, entre otros) | Saenz Peña (A) y Agüero (D), de 2019 a 2022 | Se repara la doble codificación UTF-8, se quitan los símbolos sueltos y se corrigen a mano los nombres incompletos. |
| **La misma estación con dos nombres** | Línea E: `Retiro E` hasta 2024, `Retiro` después | Se unifica como `RETIRO`. |
| **Filas sin fecha ni línea** | 2018: 78.207; 2020: 1.836 | Se descartan. |
| **Líneas vacías** | Enero de 2025 (DEH): 82.305 | Se descartan (se cuentan como "sin fecha"). |
| **Línea `Prueba`** y fechas posteriores al 31/8/2026 | 2025 y 2026 | Se descartan: 1 pasajero en 2025 y 4 en 2026. |
| **Fechas fuera del mes del archivo** | Julio de 2026 (ABC): 2 filas | Se conservan con su fecha. |

---

## 3. Resultado de la limpieza

Cada año se agregó a **una fila por fecha, hora, línea y estación**: se suman los molinetes de cada estación y los cuatro tramos de 15 minutos de cada hora.

| Año | Filas originales | Filas procesadas | Tamaño | Días con datos | Pasajeros | Promedio por día |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2015 | 10.958.582 | (completar) | (completar) | 365 | 282.519.120 | 774.025 |
| 2016 | 11.542.322 | (completar) | (completar) | 366 | 314.418.191 | 859.066 |
| 2017 | 11.938.476 | 547.713 | 5,0 MB | 365 | 328.701.725 | 900.553 |
| 2018 | 12.136.454 | 561.732 | 5,1 MB | 365 | 348.400.114 | 954.521 |
| 2019 | 12.662.343 | 589.004 | 5,4 MB | 362 | 341.340.501 | 942.930 |
| 2020 | 5.781.006 | 359.496 | 2,7 MB | 366 | 77.504.971 | 211.762 |
| 2021 | 8.071.680 | 426.415 | 3,4 MB | 364 | 96.077.158 | 263.948 |
| 2022 | 12.136.381 | 597.791 | 5,1 MB | 365 | 231.459.457 | 634.135 |
| 2023 | 12.047.696 | 583.852 | 5,0 MB | 364 | 243.225.292 | 668.201 |
| 2024 | 11.440.440 | 579.277 | 4,9 MB | 364 | 201.386.688 | 553.260 |
| 2025 | 13.279.071 | 585.316 | 5,1 MB | 365 | 206.616.375 | 566.072 |
| 2026 (hasta 31/8) | 9.951.035 | 397.591 | 3,5 MB | 243 | 133.525.596 | 549.488 |
| **Total** | **131.945.486** | | | **4.254** | **2.805.175.188** | |

*Los valores de 2015 y 2016 marcados "(completar)" están en la salida de la sección 16 del notebook.*

**Días sin datos en los originales** (7 en total): 3 en 2019 (1 en abril y 2 en mayo), 1 en noviembre de 2021, 1 en agosto de 2023, y 2 en 2024 (1 en mayo y 1 en octubre). No se pueden recuperar. Por eso los promedios se calculan por **día con datos** y no por día del calendario.

---

## 4. Controles de calidad

**Comparación con valores de referencia** calculados antes con otro método para 2019, 2020, 2021, 2025 y 2026: los 9 controles dan OK.

| Control | Esperado | Obtenido |
| :--- | ---: | ---: |
| Pasajeros totales | 855.064.366 | 855.064.601 |
| Fechas distintas | 1.700 | 1.700 |
| Promedio diario, febrero de 2020 | 767.900 | 767.869 |
| Promedio diario, abril de 2020 | 28.400 | 28.430 |
| Promedio diario, abril de 2019 | 965.900 | 965.933 |
| Promedio diario, agosto de 2025 | 610.600 | 610.572 |
| Promedio diario, agosto de 2026 | 586.500 | 586.520 |
| Total, enero de 2019 | 22.849.359 | 22.849.359 |
| Total, abril de 2020 | 852.910 | 852.910 |

La diferencia en pasajeros totales (235 sobre 855 millones) es despreciable.

**Estaciones que no aparecen todos los años (control C).** Después de corregir los nombres, solo quedan casos reales o despreciables:
- **Estaciones inauguradas en el período:** Santa Fe (H) desde 2016; Facultad de Derecho (H) desde 2018; Catalinas, Correo Central y Retiro (E) desde 2019; Premetro (`COCHEPM` y `SAGUIER`) desde 2025.
- **Registros sueltos mal asignados en el original:** `LORIA` en las líneas B, C, D, E y H en 2025, y `ND` en la línea H en 2025 y 2026. Suman menos de 100 pasajeros.
- **Plaza de Mayo (línea A) no tiene datos en 2020.** Se revisa en la sección 8 de `notebooks/exploracion_inicial.ipynb`.

**Prueba del domingo (control B):** (completar con la salida).

**Total original contra procesado (control D).** Se sumaron los pasajeros de los archivos originales de 2019 y 2020 sin pasar por la limpieza:

| Año | Original | Procesado |
| :--- | ---: | ---: |
| 2019 | 341.340.501 | 341.340.501 |
| 2020 | 77.504.971 | 77.504.971 |

Coinciden exactamente: la limpieza no pierde ni duplica pasajeros, y las 1.836 filas sin fecha descartadas en 2020 no tenían pasajeros.

---

## 5. Archivos de esta carpeta

### `por_anio/molinetes_AAAA.csv.gz`

Un archivo por año, de 2015 a 2026, comprimido con gzip (`pd.read_csv` lo lee directamente). Cada fila es **una estación en una hora de un día**; no hay dos filas con la misma fecha, hora, línea y estación.

| Columna | Tipo | Contenido |
| :--- | :--- | :--- |
| `fecha` | texto `AAAA-MM-DD` | Día, ya corregido. |
| `hora` | entero (0 a 23) | Hora de inicio del tramo (`08:15` → 8). |
| `linea` | texto | `LineaA`, `LineaB`, `LineaC`, `LineaD`, `LineaE`, `LineaH` o `LineaPM`. |
| `estacion` | texto | Nombre unificado: mayúsculas, sin acentos, sin sufijo de línea (por ejemplo, `SAENZ PENA`, `AGUERO`, `CONSTITUCION`). |
| `pax_pagos` | entero | Pasajeros pagos. |
| `pax_pases_pagos` | entero | Pasajeros con abono (tarifa social, maestros, estudiantes). |
| `pax_franq` | entero | Pasajeros franquiciados (jubilados, personas con discapacidad, menores de 3 años, entre otros). |
| `total` | entero | Pasajeros totales. |

La definición de las categorías de pasajeros y sus límites están en `data/README.md`, sección 3.

### `resumen_limpieza.csv`

Una fila por cada CSV original procesado (126 filas).

| Columna | Contenido |
| :--- | :--- |
| `anio` | Año. |
| `archivo` | Nombre del CSV dentro del zip. |
| `metodo_fecha` | Cómo se resolvió la fecha: `iso`, `dia/mes`, `secuencia` o `mes del archivo`. |
| `filas` | Filas leídas. |
| `filas_sin_columnas` | Filas rotas, sin la columna de fecha. |
| `filas_sin_fecha` | Filas con la fecha vacía (se descartan). |
| `filas_fuera_de_mes` | Filas cuya fecha no cae en el mes del nombre del archivo (desde 2022). |
| `pasajeros` | Pasajeros sumados, antes de los filtros finales. |

### `estaciones_por_anio.csv`

Una fila por cada forma en que apareció escrita una estación en cada año.

| Columna | Contenido |
| :--- | :--- |
| `anio` | Año. |
| `linea` | Línea unificada. |
| `estacion` | Nombre unificado. |
| `estacion_original` | Nombre tal como venía en el archivo original. |
| `total` | Pasajeros con ese nombre original en ese año. |

Sirve para revisar la unificación de nombres: por ejemplo, ver todas las formas originales que quedaron como `SAENZ PENA`.

### Fuera de esta carpeta

El reporte completo de la inspección (`inspeccion_resultado.txt`) queda en Google Drive, en `Mi unidad/TP-Subte/`. Su contenido es la salida de la Parte 1 del notebook, visible en GitHub.

---

## 6. Para tener en cuenta en el análisis

- **Plaza de Mayo (A) en 2020** no tiene datos, y en 2018 tiene bastantes menos pasajeros que en los años vecinos (sección 8 de la exploración).
- **2024 tiene meses atípicos:** en enero y febrero las líneas D, E y H suman bastantes menos pasajeros que en 2023, y en junio caen todas las líneas. Puede deberse a cierres, paros o faltantes; hay que verificarlo antes de interpretarlo.
- **"INCLUYEOTROMODOSDEPAGO":** desde diciembre de 2024 los archivos llevan ese nombre, pero la serie no muestra un salto en esa fecha (noviembre: 557 mil pasajeros por día; diciembre: 502 mil, la baja habitual de fin de año).
- **Total contra suma de categorías:** solo difiere en junio de 2026, en las validadoras a bordo del Premetro (`COCHEPM`); viene del archivo original (sección 7 de la exploración).
- **Premetro:** aparece desde 2025. Para comparar entre años conviene usar solo las líneas A, B, C, D, E y H.
- **Los datos cuentan entradas por molinete**, no viajes completos ni personas distintas.
