# Resultados de la exploración inicial

Resumen de lo que mostró `notebooks/exploracion_inicial.ipynb` (corrida del 1 de noviembre de 2026) sobre los datos procesados de `data/processed/por_anio/`. Cubre el punto 3.1 de la consigna (carga, estructura, cobertura y calidad) y dos controles adicionales: si el total coincide con la suma de las categorías de pasajeros y qué estaciones tienen años o meses sin datos.

Cómo se generaron los datos procesados, y qué problemas tenían los archivos originales: `data/processed/README.md` y `data/README.md`.

---

## 1. Qué se cargó

Los 12 archivos anuales (2015 a 2026) se unieron en un solo DataFrame:

| | |
| :--- | :--- |
| Filas | **6.296.891**: una por fecha, hora, línea y estación |
| Columnas | **14**: 8 de los datos procesados y 6 creadas a partir de la fecha |
| Memoria | 432 MB, después de pasar línea, estación, nombre del día y tipo de día a `category` |
| Período | del **1/1/2015 al 31/8/2026** |
| Días con datos | **4.254** de los 4.261 del período: faltan 7 (sección 3) |
| Líneas | A, B, C, D, E, H y Premetro (PM) |

---

## 2. Estructura y tipos de datos

| Columna | Tipo | Origen | Contenido |
| :--- | :--- | :--- | :--- |
| `fecha` | `datetime64` | datos procesados | Día. |
| `hora` | `int64` | datos procesados | Hora de inicio del tramo, de 0 a 23. |
| `linea` | `category` | datos procesados | `LineaA` … `LineaH`, `LineaPM`. |
| `estacion` | `category` | datos procesados | Nombre unificado de la estación. |
| `pax_pagos` | `int64` | datos procesados | Pasajeros pagos. |
| `pax_pases_pagos` | `int64` | datos procesados | Pasajeros con abono. |
| `pax_franq` | `int64` | datos procesados | Pasajeros franquiciados. |
| `total` | `int64` | datos procesados | Pasajeros totales. |
| `anio` | `int32` | creada | Año de la fecha. |
| `mes` | `int32` | creada | Mes de la fecha. |
| `periodo` | `period[M]` | creada | Año y mes (`2019-04`), para series mensuales. |
| `dia_semana` | `int32` | creada | 0 = lunes … 6 = domingo. |
| `nombre_dia` | `category` | creada | Nombre del día. |
| `tipo_dia` | `category` | creada | "hábil" (lunes a viernes) o "fin de semana". No distingue feriados. |

Las variables de pasajeros son **cuantitativas discretas** (conteos). `linea`, `estacion`, `nombre_dia` y `tipo_dia` son **cualitativas nominales**. `fecha`, `anio`, `mes` y `periodo` son **temporales**. `hora` puede tratarse como numérica o como categoría ordenada.

---

## 3. Cobertura

**Temporal.** Hay datos de todos los meses entre enero de 2015 y agosto de 2026. Faltan **7 días completos** en los archivos originales:

| Año | Mes | Días faltantes |
| :--- | :--- | ---: |
| 2019 | abril | 1 |
| 2019 | mayo | 2 |
| 2021 | noviembre | 1 |
| 2023 | agosto | 1 |
| 2024 | mayo | 1 |
| 2024 | octubre | 1 |

Por eso los promedios se calculan por **día con datos** y no por día del calendario.

**Geográfica.** 7 líneas. Algunas estaciones aparecen recién durante el período:
- Santa Fe (H) desde 2016.
- Facultad de Derecho (H) desde 2018.
- Catalinas, Correo Central y Retiro (E) desde 2019.
- El Premetro aparece en los datos recién en junio de 2025, y solo en algunos meses (sección 6).

---

## 4. Calidad general

- **Nulos:** ninguno en las 14 columnas.
- **Duplicados:** ninguno. No hay dos filas con la misma fecha, hora, línea y estación.
- **Valores fuera de rango:** ninguno. No hay pasajeros negativos y la hora va de 0 a 23.

**Resumen estadístico** (cada fila es una estación en una hora de un día):

| | `hora` | `pax_pagos` | `pax_pases_pagos` | `pax_franq` | `total` |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Media | 13,9 | 424,2 | 1,6 | 19,7 | 445,5 |
| Desvío estándar | 5,3 | 660,0 | 4,3 | 28,4 | 680,5 |
| Mínimo | 0 | 0 | 0 | 0 | 0 |
| 25 % | 9 | 80 | 0 | 3 | 85 |
| Mediana | 14 | 221 | 0 | 10 | 235 |
| 75 % | 18 | 536 | 1 | 25 | 567 |
| Máximo | 23 | 17.834 | 293 | 12.459 | 17.980 |

Qué muestra:
- **Distribución muy asimétrica.** La media de `total` (445) duplica la mediana (235) y el desvío supera a la media. La mayoría de las estaciones y horas tienen pocos pasajeros, y unas pocas estaciones en hora pico tienen muchísimos. Para describir un valor típico conviene la mediana.
- **Composición de los pasajeros** en todo el período: **pagos 95,2 %**, **franquiciados 4,4 %** y **abonados 0,4 %**. Se calcula con las medias, que es lo mismo que con los totales porque todas las columnas tienen las mismas filas.
- **Un máximo llamativo en franquiciados:** 12.459 en una sola estación y hora, cuando el 75 % de las filas tiene 25 o menos. Hay que ver a qué estación y fecha corresponde (sección 7).

---

## 5. ¿El total es la suma de las categorías?

`total` debería ser igual a `pax_pagos + pax_pases_pagos + pax_franq`.

| | |
| :--- | :--- |
| Filas que no cumplen | **275** de 6.296.891 (0,0044 %) |
| Diferencia | **612 pasajeros** de más en `total`, el 0,0005 % de los pasajeros de 2026 |
| Dónde | Todas en **junio de 2026**, **línea PM**, `COCHEPM` |
| Tamaño | Entre 1 y 9 pasajeros por fila (hora) |

`COCHEPM` no es una estación: son las validadoras ubicadas **dentro de los coches del Premetro** (molinetes `LineaPrem_Coche7_Val3`, `LineaPrem_Coche17_Val4`, etc.).

**Verificación en el archivo original.** El archivo de junio de 2026 de la línea PM tiene 36.558 registros de 15 minutos; **542 no cierran**, con **la misma diferencia de 612 pasajeros**. El problema viene de los datos de SBASE; la limpieza no lo generó (agrupar por hora junta varios registros de 15 minutos en una fila, por eso 542 pasan a 275).

**Decisión:** para contar pasajeros se usa `total`. Para la composición por tipo de pasajero se usa como base la suma de las tres categorías. El Premetro se excluye de las comparaciones entre años.

---

## 6. Estaciones con años o meses sin datos

Se comparó, para cada estación y año, los días con datos contra los días con datos de toda la red. **138 combinaciones de estación y año** quedaron marcadas, por no tener datos o por tener datos en menos del 90 % de los días. Aparecen cuatro situaciones:

1. **Estaciones con pocos días en 2020 y 2021**, durante la pandemia. Por ejemplo: Alberti (A) con 27 % de los días en 2020 y 37 % en 2021; Carabobo (A) con 31 % y 52 %; Venezuela (H) con 51 % en 2021.
2. **Estaciones nuevas**, con pocos días en su primer año.
3. **El Premetro** (`COCHEPM` y `SAGUIER`): datos en 61 días de 2025 (17 %) y 149 de 2026 (61 %). Solo hay archivos de algunos meses.
4. **Estaciones con huecos en otros años**, como Acoyte (A) en 2023, con el 83 % de los días.

*(Completar con el recuento por año: `tabla_huecos.groupby("anio").size()`, y con la lista de los casos fuera de 2020-2021: `tabla_huecos[~tabla_huecos["anio"].isin([2020, 2021])]`.)*

### 6.1 Plaza de Mayo (línea A)

| Período | Qué muestran los datos |
| :--- | :--- |
| 2015 a 2017 | Completa: entre 5,6 y 5,9 millones de pasajeros por año. |
| **Julio a noviembre de 2018** | Casi sin datos: 9 días en julio, 4 en agosto, 1 en septiembre, 5 en octubre y 16 en noviembre. De agosto a octubre, 0 pasajeros. Vuelve a la normalidad en diciembre. |
| **Diciembre de 2019 a julio de 2021** | Diciembre de 2019: 1 día con 0 pasajeros. **2020: sin ningún dato.** Enero a abril de 2021: sin datos. Mayo y junio de 2021: 1 y 2 días con 0 pasajeros. Julio de 2021: 23 días. Desde agosto de 2021, completa. |
| 2022 en adelante | Completa, con alrededor de 3,3 a 3,8 millones de pasajeros por año, bastante menos que antes de 2019. |

**¿Es un problema de la limpieza?** No. En el archivo original de 2020, la línea A tiene 17 estaciones y **ninguna es Plaza de Mayo**; la única estación con "Mayo" en el nombre es Avenida de Mayo, de la línea C. La estación directamente no está en los datos de ese año.

El mismo archivo original muestra **Saenz Peña** escrita de dos formas: `Saenz Peña` (3 pasajeros) y `Saenz Pe�a` (484.650). Confirma el problema de nombres dañados que se corrigió en la limpieza.

### 6.2 Agüero (línea D)

| Período | Qué muestran los datos |
| :--- | :--- |
| 2015 a 2019 | Completa: alrededor de 300 mil pasajeros por mes. |
| **Marzo de 2020 a agosto de 2021** | Marzo de 2020: 20 días. Desde abril de 2020 hasta agosto de 2021, solo algunos días con registros, todos con 0 pasajeros. Septiembre de 2021: 26 días (67 mil pasajeros). Desde octubre de 2021, completa. |
| **Mediados de 2023** | Cambio de nivel: de unos 300 mil pasajeros por mes (marzo a mayo) a unos 220 a 230 mil desde julio. |
| **Enero y febrero de 2024** | Enero: 7 días (26 mil pasajeros). Febrero: sin datos. |
| Marzo de 2024 a agosto de 2025 | Completa, con entre 100 y 185 mil pasajeros por mes (los más bajos: junio de 2024 y enero y febrero de 2025): alrededor de la mitad que antes de la pandemia. |
| **Septiembre de 2025 a principios de febrero de 2026** | Sin datos de septiembre a diciembre de 2025 ni en enero de 2026. Febrero de 2026: 21 días. |

### 6.3 Qué significa para el análisis

Una estación sin datos durante meses baja los totales de su línea y de la red en ese período. Eso **no es una caída de la demanda**. Para comparar estaciones o líneas entre años, hay que tener en cuenta estos huecos o comparar solo períodos en que la estación funcionó.

---

## 7. Para investigar con fuentes externas

Los datos muestran **qué** pasó, pero no **por qué**. Estos puntos necesitan contexto antes de interpretarlos en el informe:

| Qué | Dónde | Posibles explicaciones a verificar |
| :--- | :--- | :--- |
| Plaza de Mayo sin datos de julio a noviembre de 2018 | Línea A | Cierre por obras u otro motivo. |
| Plaza de Mayo sin datos de diciembre de 2019 a julio de 2021 | Línea A | Cierre por obras, cierre durante la pandemia o ambos. |
| Plaza de Mayo con menos pasajeros desde 2022 que antes de 2019 | Línea A | Cambio en la demanda, cambios en accesos. |
| Agüero sin datos de abril de 2020 a agosto de 2021 | Línea D | Cierre durante la pandemia. |
| Agüero con un cambio de nivel desde julio de 2023 | Línea D | Cierre parcial de accesos, obras, cambio en la medición. |
| Agüero sin datos en enero y febrero de 2024 y de septiembre de 2025 a febrero de 2026 | Línea D | Cierres por obras. |
| Muchas estaciones con pocos días en 2020 y 2021 | Todas las líneas | Estaciones cerradas durante la pandemia. |
| Caída de las líneas D, E y H en enero y febrero de 2024 | Líneas D, E y H | El cierre de Agüero explica una parte; puede haber otras estaciones cerradas. |
| Caída de todas las líneas en junio de 2024 | Toda la red | Paros, cambios de tarifa u otros eventos. |
| Máximo de 12.459 franquiciados en una estación y hora | Por identificar | Ver qué día y estación es (`datos.sort_values("pax_franq", ascending=False).head(10)`); un valor así puede corresponder a una apertura de molinetes registrada como franquicia. |
| Diferencia entre `total` y la suma de categorías | Premetro, junio de 2026 | Algún medio de pago que no entra en las tres categorías. Desde diciembre de 2024 los archivos dicen "INCLUYEOTROMODOSDEPAGO". |
| Premetro solo en algunos meses de 2025 y 2026 | Línea PM | Si SBASE publica esos datos desde esa fecha o si faltan archivos. |

---

## 8. Decisiones para el análisis

- **Contar pasajeros** con `total`.
- **Composición por tipo de pasajero** con la suma de las tres categorías como base, para que los porcentajes sumen 100.
- **Comparaciones entre años** solo con las líneas A, B, C, D, E y H, sin el Premetro.
- **Promedios** por día con datos, no por día del calendario.
- **Comparaciones por estación:** tener en cuenta los períodos sin datos de la sección 6.
- **Medida típica:** la mediana, por la asimetría de la distribución.
- **Interpretación:** los datos cuentan **entradas por molinete**, no viajes completos ni personas distintas, y el análisis es descriptivo, así que no permite atribuir causas.
