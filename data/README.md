# Datos: viajes en subte por molinete

- **Fuente:** [Subte - viajes por molinete](https://data.buenosaires.gob.ar/dataset/subte-viajes-molinetes), SBASE, Gobierno de la Ciudad de Buenos Aires.
- **Licencia:** CC-BY-2.5-AR.

## Cómo reproducir

1. Descargar cada recurso anual desde la página del dataset (años 2015 a 2026).
2. Guardarlo en `data/raw/` como `molinetes-AAAA.zip`.
3. Comparar el SHA-256 con el de `data/MANIFEST.md` para confirmar que es el mismo archivo.

Los zips **no se versionan**: GitHub rechaza archivos de más de 100 MB y, descomprimido, cada año pesa entre 0,5 y 1,2 GB. En el repositorio solo está el CSV agregado de `data/processed/`, generado con `src/limpieza.py`.

## Contenido

Pasajeros por molinete y estación en tramos de 15 minutos, discriminados en `pax_pagos`, `pax_pases_pagos`, `pax_franq` y `pax_TOTAL`. La definición exacta de cada columna está en el diccionario de datos de la página del dataset.

## Calidad de los datos

**Formatos distintos por año.** 2019 usa coma y fecha ISO (2019-01-01) y trae columnas `periodo` y `total`. 2020 usa coma, `FECHA` en mayúsculas y `pax_TOTAL`. 2021 usa `;` y trae `periodo`. 2025 y 2026 usan `;`, tienen BOM y cada línea completa está entre comillas. En 2026 aparece una columna extra `origen`, y la hora puede venir sin segundos (12:15).

**Fechas inconsistentes dentro del mismo archivo.**
- 2020: enero y febrero vienen como día/mes/año con ceros (01/02/2020); de marzo a octubre vienen como mes/día/año sin ceros (3/13/2020); noviembre y diciembre vuelven a día/mes/año (1/11/2020).
- 2021: algunos tramos son día/mes/año (1/4/2021) y otros son ISO con día y mes invertidos cuando el día es 12 o menos (2021-01-02 significa 1 de febrero).
- Un `pd.to_datetime` directo pierde o desordena meses enteros. Con la lectura ingenua, abril de 2020 quedaba con 8 días y agosto de 2025 mostraba una caída falsa.

**Otros problemas.** Marzo de 2025 trae `;;;;;;;;;` de más al final de cada línea. Septiembre de 2025 contiene al menos una línea en codificación latin-1 dentro de un archivo UTF-8. 2020 tiene 1.836 filas sin fecha ni línea. Existe una línea llamada `Prueba` con 2 filas y unos pocos registros con fecha posterior al 31/8/2026 (menos de 250 pasajeros en total). Abril y mayo de 2019 muestran 29 días en lugar de 30 y 31, es decir que faltan días en el original.

**Tamaño.** Hay que leer en bloques (`chunksize`) y agregar antes de analizar.

**Años sin inspeccionar.** Los hallazgos de arriba corresponden a 2019, 2020, 2021, 2025 y 2026. Los años 2015 a 2018 y 2022 a 2024 todavía no fueron revisados y pueden traer otros formatos. Completar esta sección al inspeccionarlos.
