"""
Subte de Buenos Aires (2015-2026): recuperación post-pandemia y patrones por día y horario.

Lee los datasets ya limpios (data/processed/por_anio/molinetes_<anio>.csv.gz) y calcula
estadísticos de resumen con .groupby().

Preguntas:
    1) ¿Recuperó el subte la demanda después de la pandemia?
    2) ¿Cómo cambia la demanda según días y horarios?

Uso (desde la raíz del repositorio):
    python analisis_subte.py

Opcional: `pip install holidays` para tratar los feriados como día no laborable.
"""
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data/processed/por_anio")
ARCHIVO = "molinetes_{anio}.csv.gz"
OUT_DIR = Path("resultados")
ANIOS = range(2015, 2027)
ANIO_BASE = 2019                      # último año "normal" previo a la pandemia

# Nombres de columna en tus CSV procesados (ajustar si difieren)
COL_FECHA = "fecha"
COL_HORA = "hora"                     # entero 0-23; si no existe, se extrae de COL_DESDE
COL_DESDE = "desde"
COL_LINEA = "linea"
COL_TOTAL = "total"                   # pasajeros por registro

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES_ES = {1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
            7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"}


# --------------------------------------------------------------------------- #
# Carga
# --------------------------------------------------------------------------- #
def cargar_datos() -> pd.DataFrame:
    """Lee los archivos anuales y devuelve totales por (fecha, hora, linea)."""
    partes = []
    for anio in ANIOS:
        ruta = DATA_DIR / ARCHIVO.format(anio=anio)
        if not ruta.exists():
            print(f"[aviso] no existe {ruta}")
            continue
        df = pd.read_csv(ruta)

        if COL_HORA not in df.columns:
            df[COL_HORA] = pd.to_numeric(df[COL_DESDE].astype(str).str.extract(r"(\d{1,2}):\d{2}")[0])
        df = df.rename(columns={COL_FECHA: "fecha", COL_HORA: "hora",
                                COL_LINEA: "linea", COL_TOTAL: "total"})
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["hora"] = df["hora"].astype(int)
        partes.append(df.groupby(["fecha", "hora", "linea"], as_index=False)["total"].sum())

    if not partes:
        raise FileNotFoundError(f"No se encontraron archivos en {DATA_DIR.resolve()}")
    return pd.concat(partes, ignore_index=True)


# --------------------------------------------------------------------------- #
# Variables derivadas
# --------------------------------------------------------------------------- #
def agregar_calendario(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["dia_semana"] = pd.Categorical(
        df["fecha"].dt.dayofweek.map(dict(enumerate(DIAS))), categories=DIAS, ordered=True)
    df["tipo_dia"] = df["dia_semana"].map(
        lambda d: "laborable" if d in DIAS[:5] else d).astype(str)
    try:  # feriados nacionales
        import holidays
        feriados = holidays.AR(years=sorted(df["anio"].unique()))
        df.loc[df["fecha"].dt.date.isin(feriados.keys()), "tipo_dia"] = "feriado"
    except ImportError:
        pass
    df["etapa"] = pd.cut(df["anio"], bins=[0, 2019, 2021, 9999],
                         labels=["1_pre (2015-19)", "2_pandemia (2020-21)", "3_post (2022+)"])
    return df


def franja_horaria(hora: pd.Series) -> pd.Series:
    return pd.cut(hora, bins=[-1, 5, 9, 15, 19, 23],
                  labels=["0-5 madrugada", "6-9 pico mañana", "10-15 valle",
                          "16-19 pico tarde", "20-23 noche"])


# --------------------------------------------------------------------------- #
# Estadísticos
# --------------------------------------------------------------------------- #
def resumen(df: pd.DataFrame, por, col: str = "total") -> pd.DataFrame:
    """Estadísticos de resumen agrupados con .groupby()."""
    out = df.groupby(por, observed=True)[col].agg(
        n="count", media="mean", mediana="median", desvio="std",
        p25=lambda x: x.quantile(0.25), p75=lambda x: x.quantile(0.75),
        minimo="min", maximo="max")
    out["cv_pct"] = out["desvio"] / out["media"] * 100
    return out.round(1)


def main():
    OUT_DIR.mkdir(exist_ok=True)

    horario = cargar_datos()                                   # fecha, hora, linea, total
    diario = horario.groupby("fecha", as_index=False)["total"].sum()
    diario = agregar_calendario(diario)
    laborables = diario[diario["tipo_dia"] == "laborable"]
    ultimo = int(diario["anio"].max())

    # ---- Pregunta 1: ¿se recuperó la demanda? -------------------------------
    # (a) Pasajeros por día laborable, por año (índice 100 = año base)
    anual = resumen(laborables, "anio")
    anual["indice_vs_base"] = (anual["media"] / anual.loc[ANIO_BASE, "media"] * 100).round(1)

    # (b) Mismo período: el último año está incompleto, se comparan solo sus meses
    meses_ult = diario.loc[diario["anio"] == ultimo, "mes"].unique()
    mismo_periodo = resumen(laborables[laborables["mes"].isin(meses_ult)], "anio")
    mismo_periodo["indice_vs_base"] = (
        mismo_periodo["media"] / mismo_periodo.loc[ANIO_BASE, "media"] * 100).round(1)

    # (c) Mes a mes contra el mismo mes del año base
    mensual = laborables.groupby(["mes", "anio"])["total"].mean().unstack("anio")
    mensual_idx = mensual.div(mensual[ANIO_BASE], axis=0).mul(100).round(1)
    mensual_idx.index = mensual_idx.index.map(MESES_ES)

    # (d) Por línea
    lin = (horario.groupby(["fecha", "linea"], as_index=False)["total"].sum()
           .merge(diario[["fecha", "anio", "tipo_dia"]], on="fecha"))
    lin = lin[lin["tipo_dia"] == "laborable"]
    por_linea = lin.groupby(["linea", "anio"])["total"].mean().unstack("anio")
    por_linea_idx = por_linea.div(por_linea[ANIO_BASE], axis=0).mul(100).round(1)

    # ---- Pregunta 2: días y horarios ----------------------------------------
    # (a) Por día de la semana y etapa
    por_dia = resumen(diario, ["etapa", "dia_semana"])
    por_dia["indice_vs_promedio_pct"] = (
        por_dia["media"] / por_dia.groupby("etapa", observed=True)["media"].transform("mean") * 100).round(1)

    # (b) Por hora (primero total por fecha y hora, luego estadísticos por grupo)
    hora_dia = (horario.groupby(["fecha", "hora"], as_index=False)["total"].sum()
                .merge(diario[["fecha", "etapa", "anio", "tipo_dia"]], on="fecha"))
    por_hora = resumen(hora_dia, ["etapa", "tipo_dia", "hora"])
    por_hora["pct_del_dia"] = (
        por_hora["media"] / por_hora.groupby(["etapa", "tipo_dia"], observed=True)["media"].transform("sum") * 100
    ).round(1)

    hora_pico = (hora_dia[hora_dia["tipo_dia"] == "laborable"]
                 .groupby(["anio", "hora"])["total"].mean().unstack("hora").idxmax(axis=1)
                 .rename("hora_pico_laborable"))

    # (c) Por franja horaria
    hora_dia["franja"] = franja_horaria(hora_dia["hora"])
    franja = hora_dia.groupby(["fecha", "etapa", "tipo_dia", "franja"], observed=True, as_index=False)["total"].sum()
    por_franja = resumen(franja, ["etapa", "tipo_dia", "franja"])
    por_franja["pct_del_dia"] = (
        por_franja["media"] / por_franja.groupby(["etapa", "tipo_dia"], observed=True)["media"].transform("sum") * 100
    ).round(1)

    # ---- Salida --------------------------------------------------------------
    tablas = {
        "p1_anual_laborables": anual,
        "p1_mismo_periodo": mismo_periodo,
        "p1_mensual_indice": mensual_idx,
        "p1_por_linea_indice": por_linea_idx,
        "p2_por_dia_semana": por_dia,
        "p2_por_hora": por_hora,
        "p2_hora_pico_por_anio": hora_pico.to_frame(),
        "p2_por_franja": por_franja,
    }
    pd.set_option("display.width", 200, "display.max_columns", 20, "display.max_rows", 200)
    for nombre, tabla in tablas.items():
        print(f"\n===== {nombre} =====")
        print(tabla)
        tabla.to_csv(OUT_DIR / f"{nombre}.csv")


if __name__ == "__main__":
    main()
