# Datos: viajes en subte por molinete

- **Fuente:** [Subte - viajes por molinete](https://data.buenosaires.gob.ar/dataset/subte-viajes-molinetes), SBASE, Gobierno de la Ciudad de Buenos Aires.
- **Licencia:** CC-BY-2.5-AR.
- **Años:** 2015 a 2026 (2026 hasta el 31 de agosto).

## Cómo reproducir

1. Descargar cada recurso anual desde la página del dataset y guardarlo en `data/raw/` como `molinetes-AAAA.zip`.
2. Comparar el SHA-256 con el de `data/MANIFEST.md` para confirmar que es el mismo archivo.
3. Desde la raíz del repositorio, correr `python src/limpieza.py`. Genera un archivo por año en `data/processed/por_anio/`.

Los zips **no se versionan**: GitHub rechaza archivos de más de 100 MB y, descomprimido, cada año pesa alrededor de 1 GB. En el repositorio solo están los datos agregados de `data/processed/`.

## Contenido

Pasajeros que pasan por cada molinete, en tramos de 15 minutos, discriminados en `pax_pagos`, `pax_pases_pagos`, `pax_franq` y `pax_TOTAL`. La definición exacta de cada columna está en el diccionario de datos de la página del dataset.

## Archivos procesados (`data/processed/`)

| Archivo | Contenido |
| :--- | :--- |
| `por_anio/molinetes_AAAA.csv.gz` | Pasajeros por fecha, hora, línea y estación. Columnas: `fecha`, `hora`, `linea`, `estacion`, `pax_pagos`, `pax_pases_pagos`, `pax_franq`, `total`. |
| `resumen_limpieza.csv` | Una fila por cada CSV original: método de fecha usado, filas leídas, filas sin fecha, filas fuera del mes y pasajeros. |
| `estaciones_por_anio.csv` | Cómo venía escrita cada estación en el original y a qué nombre unificado se llevó. Sirve para revisar la unificación. |

## Cómo vienen los originales

| Años | Archivos | Separador | Fecha |
| :--- | :--- | :--- | :--- |
| 2015, 2018, 2019 | uno por año | `,` | `AAAA-MM-DD` |
| 2016, 2017 | uno por año | `,`, cada campo entre comillas | `DD/MM/AAAA`, filas desordenadas |
| 2020 | uno por año | `,` | mezcla de `DD/MM/AAAA` y `M/D/AAAA` |
| 2021 | uno por año | `;` | mezcla de `D/M/AAAA` y `AAAA-DD-MM` invertida |
| 2022 a 2026 | uno por mes y por grupo de líneas (ABC, DEH y, desde 2025, PM) | `;` | `D/M/AAAA`, filas desordenadas dentro del mes |

## Calidad de los datos

**Fechas inconsistentes dentro del mismo archivo.**
- 2020: enero y febrero vienen como día/mes/año con ceros (01/02/2020); de marzo a octubre vienen como mes/día/año sin ceros (3/13/2020); noviembre y diciembre vuelven a día/mes/año (1/11/2020).
- 2021: algunos tramos son día/mes/año (1/4/2021) y otros son ISO con día y mes invertidos cuando el día es 12 o menos (2021-01-02 significa 1 de febrero).
- Agosto de 2025: la primera mitad del mes viene como día/mes y la segunda como mes/día (8/13/2025).
- Un `pd.to_datetime` directo pierde o desordena meses enteros.

**Cómo se corrigieron las fechas** (`src/limpieza.py`):
- 2015 a 2019: el formato es fijo, se lee directamente.
- 2020 y 2021: el archivo está ordenado por fecha, así que cada fecha ambigua se resuelve eligiendo la lectura más cercana al día siguiente de la fecha anterior. Es una inferencia, no un dato oficial.
- 2022 a 2026: cada archivo es de un mes, que figura en su nombre (`202508_...`). Se elige la lectura de la fecha que cae en ese mes. Las filas cuya fecha no cae en el mes del archivo se cuentan en `resumen_limpieza.csv`.

**Formatos y columnas.**
- Los nombres de las columnas cambian: `FECHA` o `fecha`, `pax_TOTAL` o `total`, `PAX_FREQ` en lugar de `pax_franq` (2016 y 2017). 2017 trae una columna de índice `V1`; 2016 y 2017 traen `ID_ESTACION`; 2015, 2019 y 2021 traen `periodo`.
- Junio de 2022 y septiembre de 2022 (DEH) traen cuatro columnas extra al principio (`HORA`, `DIA`, `TIPO_DIA`, `¿Fuera de rango?`).
- Agosto de 2026 trae una columna extra `origen`.
- Desde 2022 los archivos mensuales traen casi siempre cada línea completa entre comillas; algunos (abril y noviembre de 2023, enero, octubre y noviembre de 2024, marzo de 2025) además tienen `;;;;;;;;;` de más al final.
- La hora viene a veces sin segundos (`12:15` en lugar de `12:15:00`).

**Nombres de líneas y estaciones.**
- La línea A aparece como `A` (2016), `LINEA_A` (2015 y 2017) y `LineaA` (el resto). Se unificó como `LineaA`.
- Las estaciones aparecen en mayúsculas o no, con o sin acentos, y desde 2022 con un sufijo de línea (`Callao.B`). Se unificaron en mayúsculas, sin acentos y sin sufijo. La tabla `estaciones_por_anio.csv` permite revisar casos que hayan quedado separados.
- Hay líneas leídas en codificación latin-1 dentro de archivos UTF-8 en 2016, 2017, 2022, 2024 y 2025: suelen ser estaciones con acentos o eñe.

**Filas para descartar.**
- 2020 tiene 1.836 filas sin fecha ni línea; 2018 tiene 78.207. Enero de 2025 (DEH) tiene 82.305 líneas vacías.
- Existe una línea llamada `Prueba` (2025 y 2026) y unos pocos registros con fecha posterior al 31/8/2026. Se descartan.

**Para tener en cuenta en el análisis.**
- **El zip de 2015 trae copias de otros años.** Además de `molinetes-2015.csv`, incluye zips internos de 2016 a 2025. La limpieza usa solo el CSV de 2015.
- **Cambio en lo que se cuenta.** Desde diciembre de 2024 los archivos se llaman `...-INCLUYEOTROMODOSDEPAGO`, lo que sugiere que desde entonces se cuentan también otros medios de pago. Un salto en esa fecha puede deberse a esto y no a más viajes. Conviene verificarlo en la página del dataset antes de sacar conclusiones.
- **Premetro.** La línea PM aparece recién desde junio de 2025 (no en todos los meses). Para comparar entre años conviene usar solo las líneas A, B, C, D, E y H.
- **Enero y febrero de 2024 (DEH)** tienen bastantes menos filas que el resto de los meses. Puede deberse a cierres de estaciones; verificar antes de interpretarlo.
- **Faltan días.** Abril y mayo de 2019 muestran 29 días en lugar de 30 y 31. La tabla de días por mes que imprime `src/limpieza.py` muestra los huecos de todos los años.
- **Tamaño.** Cada año descomprimido pesa alrededor de 1 GB: hay que leer por bloques y agregar antes de analizar.
