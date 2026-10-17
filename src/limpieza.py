"""
Limpieza y agregación de los datos de molinetes del subte de Buenos Aires.

Para cada año:
1. Abre el zip original (sin descomprimirlo en disco) y recorre cada CSV fila por fila.
2. Corrige la fecha según cómo viene escrita en ese año (ver FORMATO_FECHA).
3. Unifica los nombres de las líneas y de las estaciones.
4. Suma los pasajeros por fecha, hora, línea y estación.
5. Guarda el resultado en data/processed/por_anio/molinetes_AAAA.csv.gz

Uso, desde la carpeta raíz del repositorio:
    python src/limpieza.py                          # zips en data/raw/, todos los años
    python src/limpieza.py CARPETA_ZIPS             # zips en otra carpeta (por ejemplo, Drive)
    python src/limpieza.py CARPETA_ZIPS 2019 2025   # solo esos años (sin controles)
    python src/limpieza.py --controles              # solo los controles, con lo ya procesado

Si el archivo de un año ya existe, ese año se saltea. Para rehacerlo, hay que borrar su archivo.
"""

import os
import io
import sys
import zipfile
import datetime as dt

import pandas as pd


CARPETA_SALIDA = os.path.join("data", "processed", "por_anio")
ARCHIVO_RESUMEN = os.path.join("data", "processed", "resumen_limpieza.csv")
ARCHIVO_ESTACIONES = os.path.join("data", "processed", "estaciones_por_anio.csv")

ANIOS = list(range(2015, 2027))
ULTIMA_FECHA = pd.Timestamp("2026-08-31")   # último día con datos reales
TAM_BLOQUE = 500_000                        # filas que se leen antes de agrupar

COLUMNAS_PAX = ["pax_pagos", "pax_pases_pagos", "pax_franq", "total"]

# Algunos años usan otros nombres para las mismas columnas.
RENOMBRAR = {"pax_freq": "pax_franq", "pax_total": "total"}

# Cómo viene escrita la fecha en los archivos anuales (hallazgos de la inspección):
#   "iso"       -> 2019-01-31, siempre año-mes-día
#   "dia/mes"   -> 31/01/2016, siempre día/mes/año (el archivo NO está ordenado por fecha)
#   "secuencia" -> mezcla día/mes, mes/día e ISO invertida; el archivo SÍ está ordenado,
#                  así que cada fecha ambigua se resuelve mirando la fecha anterior.
# Desde 2022 hay un CSV por mes (por ejemplo 202508_PAX15min-ABC.csv): la fecha se
# resuelve con el año y el mes que figuran al principio del nombre del archivo.
FORMATO_FECHA = {
    2015: "iso", 2018: "iso", 2019: "iso",
    2016: "dia/mes", 2017: "dia/mes",
    2020: "secuencia", 2021: "secuencia",
}

# Valores de control calculados antes con 2019, 2020, 2021, 2025 y 2026 (método anterior).
CONTROLES = {
    "Pasajeros totales": 855_064_366,
    "Fechas distintas": 1_700,
    "Promedio diario feb-2020": 767_900,
    "Promedio diario abr-2020": 28_400,
    "Promedio diario abr-2019": 965_900,
    "Promedio diario ago-2025": 610_600,
    "Promedio diario ago-2026": 586_500,
    "Total ene-2019": 22_849_359,
    "Total abr-2020": 852_910,
}


# ---------------------------------------------------------------------------
# 1. Fechas
# ---------------------------------------------------------------------------

def fecha_valida(anio, mes, dia):
    """Devuelve la fecha si existe, o None si es imposible (por ejemplo, mes 13)."""
    try:
        return dt.date(anio, mes, dia)
    except ValueError:
        return None


def lecturas_posibles(texto):
    """
    Devuelve las dos lecturas de una fecha: [normal, invertida].
    Con guiones: normal = AAAA-MM-DD, invertida = AAAA-DD-MM.
    Con barras:  normal = DD/MM/AAAA, invertida = MM/DD/AAAA.
    Una lectura imposible queda como None.
    """
    texto = texto.strip().strip('"').split(" ")[0]   # por si viene con hora
    try:
        if "-" in texto:
            a, b, c = [int(x) for x in texto.split("-")[:3]]
            return [fecha_valida(a, b, c), fecha_valida(a, c, b)]
        if "/" in texto:
            a, b, c = [int(x) for x in texto.split("/")[:3]]
            return [fecha_valida(c, b, a), fecha_valida(c, a, b)]
    except ValueError:
        pass
    return [None, None]


def mas_cercana(candidatas, objetivo):
    """De las fechas posibles, la más cercana al objetivo."""
    validas = [f for f in candidatas if f is not None]
    if not validas:
        return None
    return min(validas, key=lambda f: abs((f - objetivo).days))


def resolver_por_mes(texto, anio, mes):
    """
    Archivos mensuales: se queda con la lectura que cae en el mes del archivo.
    Devuelve (fecha, fuera_de_mes). Si ninguna lectura cae en el mes, usa la más
    cercana a ese mes y lo marca para el resumen.
    """
    candidatas = [f for f in lecturas_posibles(texto) if f is not None]
    for f in candidatas:
        if f.year == anio and f.month == mes:
            return f, False
    return mas_cercana(candidatas, dt.date(anio, mes, 15)), True


# ---------------------------------------------------------------------------
# 2. Lectura de las líneas del archivo
# ---------------------------------------------------------------------------

def leer_lineas(zf, nombre):
    """
    Lee el CSV línea por línea dentro del zip.
    - Saca el BOM de la primera línea.
    - Si una línea no es UTF-8 válido, la lee como latin-1 (pasa en varios años).
    - Si la línea ENTERA está entre comillas (2023 a 2026), saca esas comillas y lo
      que sobre después, como los ';;;;;;;;;' de marzo de 2025. Si cada campo tiene
      sus propias comillas (2016), la deja igual: pandas las entiende solo.
    """
    primera = True
    with zf.open(nombre) as archivo:
        for crudo in archivo:
            try:
                linea = crudo.decode("utf-8-sig" if primera else "utf-8")
            except UnicodeDecodeError:
                linea = crudo.decode("latin-1")
            primera = False
            linea = linea.strip()
            if linea.startswith('"'):
                ultima_comilla = linea.rfind('"')
                interior = linea[1:ultima_comilla]
                if ultima_comilla > 0 and '"' not in interior:
                    linea = interior
            yield linea


# ---------------------------------------------------------------------------
# 3. Nombres de líneas y estaciones
# ---------------------------------------------------------------------------

def normalizar_linea(serie):
    """'A', 'LINEA_A' y 'LineaA' pasan a ser 'LineaA'. 'PM' y 'LineaPM' pasan a 'LineaPM'."""
    letra = serie.str.upper().str.replace("LINEA", "", regex=False)
    letra = letra.str.replace("_", "", regex=False).str.strip()
    return "Linea" + letra


ACENTOS = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U", "Ñ": "N"}


def normalizar_estacion(serie):
    """
    Unifica cómo se escribe una estación entre años:
    'Plaza Miserere' y 'PLAZA MISERERE' -> 'PLAZA MISERERE'
    'Constitución' -> 'CONSTITUCION'
    'Callao.B' -> 'CALLAO' (la línea ya está en su propia columna)
    """
    nombre = serie.str.upper().str.strip()
    for con_acento, sin_acento in ACENTOS.items():
        nombre = nombre.str.replace(con_acento, sin_acento, regex=False)
    nombre = nombre.str.replace(r"\.[A-Z]{1,2}$", "", regex=True)   # sufijo de línea
    nombre = nombre.str.replace(".", " ", regex=False)
    nombre = nombre.str.split().str.join(" ")                       # espacios dobles
    return nombre


# ---------------------------------------------------------------------------
# 4. Procesamiento de un CSV
# ---------------------------------------------------------------------------

def agrupar_bloque(buffer, sep, columnas):
    """Convierte un bloque de líneas en DataFrame y lo agrupa por fecha, hora, línea y estación."""
    df = pd.read_csv(io.StringIO("\n".join(buffer)), sep=sep, names=columnas,
                     header=None, dtype=str, on_bad_lines="skip")
    for columna in COLUMNAS_PAX:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d", errors="coerce")
    df["hora"] = pd.to_numeric(df["desde"].str.split(":").str[0], errors="coerce")
    df = df[df["fecha"].notna() & df["linea"].notna() & df["estacion"].notna()].copy()

    df["estacion_original"] = df["estacion"].str.strip()
    df["linea"] = normalizar_linea(df["linea"])
    df["estacion"] = normalizar_estacion(df["estacion"])

    agregado = df.groupby(["fecha", "hora", "linea", "estacion"], as_index=False)[COLUMNAS_PAX].sum()
    nombres = df.groupby(["linea", "estacion", "estacion_original"], as_index=False)["total"].sum()
    return agregado, nombres


def procesar_csv(zf, nombre, anio):
    """Recorre un CSV, corrige las fechas y devuelve (agregado, nombres, fila_resumen)."""
    lineas = leer_lineas(zf, nombre)
    encabezado = next(lineas, None)
    if encabezado is None:
        return None

    sep = ";" if encabezado.count(";") > encabezado.count(",") else ","
    columnas = [c.strip().strip('"').lower() for c in encabezado.split(sep)]
    columnas = [RENOMBRAR.get(c, c) for c in columnas]
    pos_fecha = columnas.index("fecha")

    nombre_base = os.path.basename(nombre)
    if anio >= 2022:
        metodo = "mes del archivo"
        anio_archivo, mes_archivo = int(nombre_base[:4]), int(nombre_base[4:6])
    else:
        metodo = FORMATO_FECHA[anio]

    cuenta = {"filas": 0, "filas_sin_columnas": 0, "filas_sin_fecha": 0, "filas_fuera_de_mes": 0}
    ya_resueltas = {}          # texto de fecha -> (fecha en ISO, fuera de mes)
    ultimo_texto, ultima_iso, anterior = None, "", None
    bloques, buffer = [], []

    for linea in lineas:
        partes = linea.split(sep, pos_fecha + 1)
        if len(partes) <= pos_fecha:          # línea vacía o rota
            cuenta["filas_sin_columnas"] += 1
            continue
        cuenta["filas"] += 1
        texto = partes[pos_fecha].strip().strip('"')

        if texto == "":
            iso = ""
        elif metodo == "secuencia":
            # El orden importa: solo se recalcula cuando el texto de la fecha cambia.
            if texto != ultimo_texto:
                if anterior is None:
                    f = lecturas_posibles(texto)[0] or lecturas_posibles(texto)[1]
                else:
                    f = mas_cercana(lecturas_posibles(texto), anterior + dt.timedelta(days=1))
                ultimo_texto = texto
                ultima_iso = f.isoformat() if f else ""
                if f:
                    anterior = f
            iso = ultima_iso
        else:
            # El orden no importa: cada texto se resuelve una sola vez y se guarda.
            if texto not in ya_resueltas:
                if metodo == "mes del archivo":
                    f, fuera = resolver_por_mes(texto, anio_archivo, mes_archivo)
                else:
                    f, fuera = lecturas_posibles(texto)[0], False
                ya_resueltas[texto] = (f.isoformat() if f else "", fuera)
            iso, fuera = ya_resueltas[texto]
            if fuera:
                cuenta["filas_fuera_de_mes"] += 1

        if iso == "":
            cuenta["filas_sin_fecha"] += 1
        partes[pos_fecha] = iso
        buffer.append(sep.join(partes))
        if len(buffer) >= TAM_BLOQUE:
            bloques.append(agrupar_bloque(buffer, sep, columnas))
            buffer = []

    if buffer:
        bloques.append(agrupar_bloque(buffer, sep, columnas))
    if not bloques:
        return None

    agregado = pd.concat([b[0] for b in bloques])
    nombres = pd.concat([b[1] for b in bloques])
    fila_resumen = {"anio": anio, "archivo": nombre, "metodo_fecha": metodo, **cuenta,
                    "pasajeros": int(agregado["total"].sum())}
    return agregado, nombres, fila_resumen


# ---------------------------------------------------------------------------
# 5. Procesamiento de un año completo
# ---------------------------------------------------------------------------

def guardar_reemplazando_anio(nuevo, ruta, anio):
    """Agrega las filas de un año a un CSV de resumen, reemplazando las anteriores de ese año."""
    if os.path.exists(ruta):
        viejo = pd.read_csv(ruta)
        nuevo = pd.concat([viejo[viejo["anio"] != anio], nuevo])
    nuevo.sort_values("anio").to_csv(ruta, index=False)


def procesar_anio(carpeta_zips, anio):
    ruta_zip = os.path.join(carpeta_zips, f"molinetes-{anio}.zip")
    ruta_salida = os.path.join(CARPETA_SALIDA, f"molinetes_{anio}.csv.gz")
    if os.path.exists(ruta_salida):
        print(f"{anio}: ya procesado ({ruta_salida}), se saltea.")
        return
    if not os.path.exists(ruta_zip):
        print(f"{anio}: no se encontró {ruta_zip}, se saltea.")
        return

    print(f"\n{anio}: procesando {ruta_zip}")
    agregados, nombres, resumen = [], [], []
    with zipfile.ZipFile(ruta_zip) as zf:
        for info in zf.infolist():
            # Solo los CSV de primer nivel. El zip de 2015 trae además copias de otros
            # años dentro de zips internos: se ignoran porque cada año tiene su propio zip.
            if not info.filename.lower().endswith(".csv"):
                continue
            resultado = procesar_csv(zf, info.filename, anio)
            if resultado is None:
                continue
            agregados.append(resultado[0])
            nombres.append(resultado[1])
            resumen.append(resultado[2])
            r = resultado[2]
            print(f"  {os.path.basename(info.filename)}: {r['filas']:,} filas, "
                  f"{r['pasajeros']:,} pasajeros, sin fecha: {r['filas_sin_fecha']:,}, "
                  f"fuera del mes: {r['filas_fuera_de_mes']:,}")

    datos = pd.concat(agregados)
    datos = datos.groupby(["fecha", "hora", "linea", "estacion"], as_index=False)[COLUMNAS_PAX].sum()

    # Filtros finales: línea de prueba, fechas de otro año y fechas posteriores al último dato real.
    antes = datos["total"].sum()
    datos = datos[datos["linea"] != "LineaPRUEBA"]
    datos = datos[(datos["fecha"].dt.year == anio) & (datos["fecha"] <= ULTIMA_FECHA)]
    print(f"  Pasajeros descartados por los filtros finales: {antes - datos['total'].sum():,.0f}")

    datos["hora"] = datos["hora"].astype(int)
    for columna in COLUMNAS_PAX:
        datos[columna] = datos[columna].round().astype("int64")
    datos["fecha"] = datos["fecha"].dt.strftime("%Y-%m-%d")

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    datos.to_csv(ruta_salida, index=False, compression="gzip")
    print(f"  Guardado {ruta_salida}: {len(datos):,} filas, "
          f"{os.path.getsize(ruta_salida) / 1_000_000:.1f} MB")

    tabla_nombres = pd.concat(nombres).groupby(["linea", "estacion", "estacion_original"],
                                               as_index=False)["total"].sum()
    tabla_nombres.insert(0, "anio", anio)
    guardar_reemplazando_anio(tabla_nombres, ARCHIVO_ESTACIONES, anio)
    guardar_reemplazando_anio(pd.DataFrame(resumen), ARCHIVO_RESUMEN, anio)


# ---------------------------------------------------------------------------
# 6. Controles
# ---------------------------------------------------------------------------

def cargar_procesados(anios):
    partes = []
    for anio in anios:
        ruta = os.path.join(CARPETA_SALIDA, f"molinetes_{anio}.csv.gz")
        if os.path.exists(ruta):
            partes.append(pd.read_csv(ruta, parse_dates=["fecha"]))
    return pd.concat(partes) if partes else None


def promedio_diario(df, anio, mes):
    del_mes = df[(df["fecha"].dt.year == anio) & (df["fecha"].dt.month == mes)]
    dias = del_mes["fecha"].nunique()
    return del_mes["total"].sum() / dias if dias else float("nan")


def total_mensual(df, anio, mes):
    return df[(df["fecha"].dt.year == anio) & (df["fecha"].dt.month == mes)]["total"].sum()


def controles():
    print("\n" + "=" * 70)
    print("CONTROLES contra los valores calculados antes (2019, 2020, 2021, 2025, 2026)")
    print("=" * 70)
    df = cargar_procesados([2019, 2020, 2021, 2025, 2026])
    if df is None:
        print("Faltan años para comparar.")
    else:
        obtenidos = {
            "Pasajeros totales": df["total"].sum(),
            "Fechas distintas": df["fecha"].nunique(),
            "Promedio diario feb-2020": promedio_diario(df, 2020, 2),
            "Promedio diario abr-2020": promedio_diario(df, 2020, 4),
            "Promedio diario abr-2019": promedio_diario(df, 2019, 4),
            "Promedio diario ago-2025": promedio_diario(df, 2025, 8),
            "Promedio diario ago-2026": promedio_diario(df, 2026, 8),
            "Total ene-2019": total_mensual(df, 2019, 1),
            "Total abr-2020": total_mensual(df, 2020, 4),
        }
        for nombre, esperado in CONTROLES.items():
            obtenido = obtenidos[nombre]
            diferencia = (obtenido - esperado) / esperado * 100
            marca = "OK" if abs(diferencia) < 0.5 else "REVISAR"
            print(f"{nombre:<26} esperado {esperado:>14,.0f}   obtenido {obtenido:>14,.0f}"
                  f"   ({diferencia:+.2f}%)  {marca}")

    print("\nPROMEDIO DIARIO POR MES (miles de pasajeros) y DÍAS CON DATOS, todos los años")
    df = cargar_procesados(ANIOS)
    if df is None:
        return
    diario = df.groupby("fecha", as_index=False)["total"].sum()
    diario["anio"] = diario["fecha"].dt.year
    diario["mes"] = diario["fecha"].dt.month
    promedio = diario.pivot_table(index="anio", columns="mes", values="total", aggfunc="mean")
    dias = diario.pivot_table(index="anio", columns="mes", values="total", aggfunc="count")
    print((promedio / 1000).round(0).to_string())
    print("\nDías con datos por mes:")
    print(dias.to_string())


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--controles":
        controles()
        return
    carpeta_zips = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "raw")
    anios = [int(a) for a in sys.argv[2:]]
    for anio in anios or ANIOS:
        procesar_anio(carpeta_zips, anio)
    if not anios:          # con todos los años, al final se muestran los controles
        controles()


if __name__ == "__main__":
    main()
