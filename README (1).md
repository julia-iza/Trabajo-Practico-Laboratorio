# ¿Recuperó el subte de Buenos Aires la demanda previa a la pandemia?

Trabajo práctico grupal. Laboratorio de Métodos Cuantitativos, Tecnicatura en Gestión y Análisis de Datos en Organizaciones (FCE-UBA), 2C 2026.

## Integrantes

| Nombre | Registro | Usuario de GitHub |
| :--- | :--- | :--- |
| (completar) | | |

## Pregunta de investigación

¿Recuperó el subte de Buenos Aires la demanda previa a la pandemia? ¿Cómo cambió cuándo (hora y día) y dónde (estación y línea) se viaja?

## Hallazgos principales

_A completar cuando el análisis esté terminado._

## Estructura del repositorio

```
data/raw/         zips originales (no se versionan)
data/processed/   CSV agregado liviano (sí se versiona)
data/README.md    fuente, cómo descargar, advertencias de calidad
data/MANIFEST.md  tamaño y SHA-256 de cada zip original
src/              limpieza.py y graficos.py
notebooks/        analisis_subte.ipynb, el notebook del TP
figuras/          gráficos exportados para el informe
informe/          informe académico
presentacion/     diapositivas (PDF o link)
```

## Cómo correrlo

1. Abrir `notebooks/analisis_subte.ipynb` en Google Colab y ejecutar todo. La primera celda clona el repositorio y el notebook carga `data/processed/molinetes_agregado.csv.gz`.
2. Para regenerar ese CSV desde los originales, seguir `data/README.md` y correr `src/limpieza.py`.

## Fuentes

- SBASE / Gobierno de la Ciudad de Buenos Aires, *Subte - viajes por molinete*, licencia CC-BY-2.5-AR.

## Limitaciones

- Los datos cuentan entradas por molinete, no viajes completos ni personas distintas.
- El análisis es descriptivo: no permite atribuir causas a los cambios de demanda.
