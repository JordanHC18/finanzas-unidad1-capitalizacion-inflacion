# Nombres y apellidos: Huaroc Cardenas Jordan Jose
# Código de matrícula: 2024200503I
# Tema N.º 20: Capitalización compuesta frente a la inflación: poder adquisitivo del ahorro peruano
# Fecha de extracción: 2026-09-25

import os
import re
import glob
import html
import hashlib

import pandas as pd
import numpy as np

from bs4 import BeautifulSoup
from io import StringIO
from datetime import datetime

# ============================================================
# PARÁMETROS CONGELADOS
# ============================================================

FECHA_INICIO = "2018-01-01"
FECHA_CORTE = "2026-08-31"

CAPITAL_INICIAL = 1000.00

SERIE_IPC = "PN38705PM"

# ============================================================
# RUTAS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RUTA_CRUDOS = os.path.join(
    BASE_DIR,
    "datos_crudos"
)

RUTA_HTML = os.path.join(
    RUTA_CRUDOS,
    "sbs_mensual"
)

RUTA_PROCESADOS = os.path.join(
    BASE_DIR,
    "datos_procesados"
)

os.makedirs(
    RUTA_PROCESADOS,
    exist_ok=True
)

ARCHIVO_IPC = os.path.join(
    RUTA_CRUDOS,
    "ipc_bcrp_PN38705PM_2024200503I.csv"
)

ARCHIVO_FINAL = os.path.join(
    RUTA_PROCESADOS,
    "datos_procesados_2024200503I.csv"
)

LOG = os.path.join(
    BASE_DIR,
    "log_ejecucion.txt"
)

# ============================================================
# NOMBRES DE BANCOS
# ============================================================

BANCOS_CLAVE = [
    "BBVA",
    "Continental",
    "Bancom",
    "Comercio",
    "Crédito",
    "Credito",
    "Pichincha",
    "BIF",
    "Scotiabank",
    "Citibank",
    "Interbank",
    "Mibanco",
    "GNB",
    "Falabella",
    "Santander",
    "Ripley",
    "Alfin",
    "ICBC",
    "Bank of China",
    "BCI",
    "Compartamos"
]

MAPEO_ENTIDADES = {
    "Continental": "BBVA",
    "BBVA": "BBVA",

    "Financiero": "Pichincha",
    "Pichincha": "Pichincha",

    "Azteca": "Alfin",
    "Alfin": "Alfin",

    "Comercio": "Bancom",
    "Bancom": "Bancom"
}

# ============================================================
# FUNCIONES SBS
# ============================================================

def encontrar_tabla_bancaria(html_texto):

    tablas = pd.read_html(
        StringIO(html_texto)
    )

    candidatos = []

    for i, tabla in enumerate(tablas):

        texto = (
            " ".join(
                str(c)
                for c in tabla.columns
            )
            + " "
            + tabla.astype(str).to_string()
        ).lower()

        puntos = sum(
            1
            for banco in BANCOS_CLAVE
            if banco.lower() in texto
        )

        if (
            puntos >= 4
            and "ahorro" in texto
        ):

            candidatos.append({
                "indice": i,
                "puntos": puntos,
                "filas": tabla.shape[0]
            })

    if len(candidatos) == 0:

        raise ValueError(
            "No se encontró tabla bancaria."
        )

    candidatos = sorted(
        candidatos,
        key=lambda x: (
            x["puntos"],
            x["filas"]
        ),
        reverse=True
    )

    indice = candidatos[0]["indice"]

    return tablas[indice].copy()


def procesar_tabla_bancaria(tabla):

    inicio_bancos = None

    for i in range(len(tabla)):

        valor = str(
            tabla.iloc[i, 0]
        ).strip()

        if any(
            banco.lower()
            in valor.lower()
            for banco in BANCOS_CLAVE
        ):

            inicio_bancos = i
            break

    if inicio_bancos is None:

        raise ValueError(
            "No se encontró inicio de bancos."
        )

    fin_bancos = None

    for i in range(
        inicio_bancos,
        len(tabla)
    ):

        valor = str(
            tabla.iloc[i, 0]
        ).strip().lower()

        if "promedio" in valor:

            fin_bancos = i
            break

    if fin_bancos is None:

        raise ValueError(
            "No se encontró Promedio."
        )

    entidades = (
        tabla.iloc[
            inicio_bancos:fin_bancos + 1,
            0
        ]
        .astype(str)
        .str.strip()
        .reset_index(drop=True)
    )

    numero = len(entidades)

    inicio_tasas = (
        inicio_bancos
        - numero
    )

    if inicio_tasas < 0:

        raise ValueError(
            "Bloque de tasas inválido."
        )

    tasas = (
        tabla.iloc[
            inicio_tasas:inicio_bancos,
            0
        ]
        .astype(str)
        .str.strip()
        .reset_index(drop=True)
    )

    df = pd.DataFrame({
        "entidad": entidades,
        "tasa_pasiva": tasas
    })

    df["tasa_pasiva"] = (
        df["tasa_pasiva"]
        .replace({
            "-": np.nan,
            "nan": np.nan,
            "": np.nan
        })
        .astype(str)
        .str.replace(
            "%",
            "",
            regex=False
        )
        .str.replace(
            ",",
            ".",
            regex=False
        )
    )

    df["tasa_pasiva"] = pd.to_numeric(
        df["tasa_pasiva"],
        errors="coerce"
    )

    df = df[
        ~df["entidad"]
        .str.contains(
            "Promedio",
            case=False,
            na=False
        )
    ].reset_index(drop=True)

    return df


# ============================================================
# LEER HTML CRUDOS SBS
# ============================================================

todos_html = sorted(
    glob.glob(
        os.path.join(
            RUTA_HTML,
            "sbs_*.html"
        )
    )
)

if len(todos_html) == 0:
    raise FileNotFoundError(
        "No existen HTML crudos de SBS."
    )

# Puede haber más de una captura del mismo mes.
# Los archivos crudos NO se borran ni se editan.
# Para procesar, se utiliza la captura con la fecha más reciente
# disponible dentro de cada año-mes.
html_por_mes = {}

for ruta in todos_html:

    nombre = os.path.basename(
        ruta
    )

    coincidencia = re.search(
        r"sbs_(\d{4})_(\d{2})_(\d{2})\.html$",
        nombre
    )

    if coincidencia is None:
        continue

    anio = int(
        coincidencia.group(1)
    )

    mes = int(
        coincidencia.group(2)
    )

    dia = int(
        coincidencia.group(3)
    )

    fecha_archivo = pd.Timestamp(
        year=anio,
        month=mes,
        day=dia
    )

    clave = (
        anio,
        mes
    )

    if (
        clave not in html_por_mes
        or fecha_archivo > html_por_mes[clave][0]
    ):
        html_por_mes[clave] = (
            fecha_archivo,
            ruta
        )

archivos_html = [
    html_por_mes[clave][1]
    for clave in sorted(
        html_por_mes
    )
]

if len(archivos_html) != 104:
    raise ValueError(
        f"Se esperaban 104 meses SBS "
        f"y se encontraron {len(archivos_html)}."
    )

resultados_sbs = []

for ruta in archivos_html:

    nombre = os.path.basename(
        ruta
    )

    coincidencia = re.search(
        r"sbs_(\d{4})_(\d{2})_(\d{2})\.html",
        nombre
    )

    if coincidencia is None:
        continue

    anio = int(
        coincidencia.group(1)
    )

    mes = int(
        coincidencia.group(2)
    )

    dia = int(
        coincidencia.group(3)
    )

    fecha_sbs = pd.Timestamp(
        year=anio,
        month=mes,
        day=dia
    )

    periodo = (
        pd.Timestamp(
            year=anio,
            month=mes,
            day=1
        )
        + pd.offsets.MonthEnd(0)
    )

    with open(
        ruta,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as archivo:

        texto = archivo.read()

    tabla = encontrar_tabla_bancaria(
        texto
    )

    df_mes = procesar_tabla_bancaria(
        tabla
    )

    df_mes.insert(
        0,
        "fecha_sbs",
        fecha_sbs
    )

    df_mes.insert(
        0,
        "periodo",
        periodo
    )

    resultados_sbs.append(
        df_mes
    )

df_sbs = pd.concat(
    resultados_sbs,
    ignore_index=True
)

# Limitar estrictamente al rango declarado.
df_sbs = df_sbs[
    (
        df_sbs["periodo"]
        >= pd.Timestamp("2018-01-31")
    )
    &
    (
        df_sbs["periodo"]
        <= pd.Timestamp("2026-08-31")
    )
].copy()

# ============================================================
# HOMOLOGAR CONTINUIDADES HISTÓRICAS
# ============================================================

df_sbs["entidad_original"] = (
    df_sbs["entidad"]
)

df_sbs["entidad_panel"] = (
    df_sbs["entidad"]
    .replace(
        MAPEO_ENTIDADES
    )
)

duplicados = (
    df_sbs
    .duplicated(
        subset=[
            "periodo",
            "entidad_panel"
        ]
    )
    .sum()
)

if duplicados != 0:

    raise ValueError(
        "Existen duplicados periodo-entidad "
        "después de homologar."
    )

# ============================================================
# PANEL BALANCEADO SOLO CON DATOS SBS OBSERVADOS
# ============================================================

TOTAL_PERIODOS = 104

cobertura = (
    df_sbs
    .groupby(
        "entidad_panel"
    )
    .agg(
        periodos=(
            "periodo",
            "nunique"
        ),
        tasas_observadas=(
            "tasa_pasiva",
            "count"
        )
    )
    .reset_index()
)

entidades_completas = (
    cobertura.loc[
        (
            cobertura["periodos"]
            == TOTAL_PERIODOS
        )
        &
        (
            cobertura["tasas_observadas"]
            == TOTAL_PERIODOS
        ),
        "entidad_panel"
    ]
    .tolist()
)

df_x1 = (
    df_sbs[
        df_sbs[
            "entidad_panel"
        ].isin(
            entidades_completas
        )
    ]
    .copy()
)

df_x1["entidad"] = (
    df_x1["entidad_panel"]
)

df_x1 = (
    df_x1[
        [
            "periodo",
            "fecha_sbs",
            "entidad",
            "tasa_pasiva"
        ]
    ]
    .sort_values(
        [
            "periodo",
            "entidad"
        ]
    )
    .reset_index(drop=True)
)

# ============================================================
# TRATAMIENTO DE OUTLIERS
#
# Se identifican mediante IQR por entidad.
# Como son datos oficiales verificables de SBS,
# NO se winsorizan ni se reemplazan.
# ============================================================

outliers_detectados = []

for entidad, grupo in df_x1.groupby(
    "entidad"
):

    q1 = grupo[
        "tasa_pasiva"
    ].quantile(0.25)

    q3 = grupo[
        "tasa_pasiva"
    ].quantile(0.75)

    iqr = q3 - q1

    inferior = q1 - 1.5 * iqr
    superior = q3 + 1.5 * iqr

    mascara = (
        (
            grupo["tasa_pasiva"]
            < inferior
        )
        |
        (
            grupo["tasa_pasiva"]
            > superior
        )
    )

    if mascara.any():

        temporal = grupo.loc[
            mascara,
            [
                "periodo",
                "entidad",
                "tasa_pasiva"
            ]
        ].copy()

        temporal["limite_inferior"] = (
            inferior
        )

        temporal["limite_superior"] = (
            superior
        )

        outliers_detectados.append(
            temporal
        )

if len(outliers_detectados) > 0:

    df_outliers = pd.concat(
        outliers_detectados,
        ignore_index=True
    )

    n_outliers = len(
        df_outliers
    )

else:

    n_outliers = 0

# ============================================================
# LEER IPC BCRP CRUDO
# ============================================================

with open(
    ARCHIVO_IPC,
    "rb"
) as archivo:

    contenido = archivo.read()

texto = contenido.decode(
    "utf-8-sig",
    errors="replace"
)

texto = (
    texto
    .replace("<br>", "\n")
    .replace("<br/>", "\n")
    .replace("<br />", "\n")
)

texto = html.unescape(
    texto
)

df_ipc_crudo = pd.read_csv(
    StringIO(texto)
)

df_ipc = (
    df_ipc_crudo
    .iloc[:, :2]
    .copy()
)

df_ipc.columns = [
    "periodo_bcrp",
    "ipc"
]

df_ipc["ipc"] = pd.to_numeric(
    df_ipc["ipc"],
    errors="coerce"
)

MESES = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "set": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12
}


def convertir_periodo(valor):

    texto = (
        str(valor)
        .strip()
        .lower()
        .replace(".", "")
        .replace(" ", "")
    )

    coincidencia = re.match(
        r"([a-záéíóúñ]+)(\d{4})$",
        texto
    )

    if coincidencia is None:

        return pd.NaT

    mes = MESES.get(
        coincidencia.group(1)[:3]
    )

    anio = int(
        coincidencia.group(2)
    )

    return (
        pd.Timestamp(
            year=anio,
            month=mes,
            day=1
        )
        + pd.offsets.MonthEnd(0)
    )


df_ipc["periodo"] = (
    df_ipc["periodo_bcrp"]
    .apply(
        convertir_periodo
    )
)

df_ipc = (
    df_ipc[
        [
            "periodo",
            "ipc"
        ]
    ]
    .sort_values(
        "periodo"
    )
    .reset_index(drop=True)
)

if (
    df_ipc["periodo"].nunique()
    != 104
):

    raise ValueError(
        "El IPC no contiene 104 periodos."
    )

# ============================================================
# UNIR SBS + BCRP
# ============================================================

df = pd.merge(
    df_x1,
    df_ipc,
    on="periodo",
    how="left",
    validate="many_to_one"
)

if df["ipc"].isna().any():

    raise ValueError(
        "Existen IPC faltantes tras la unión."
    )

# ============================================================
# TRANSFORMACIONES FINANCIERAS
# ============================================================

df["tasa_pasiva_decimal"] = (
    df["tasa_pasiva"]
    / 100
)

df["tasa_mensual"] = (
    (
        1
        + df["tasa_pasiva_decimal"]
    ) ** (1 / 12)
    - 1
)

df["tasa_mensual_pct"] = (
    df["tasa_mensual"]
    * 100
)

df = (
    df
    .sort_values(
        [
            "entidad",
            "periodo"
        ]
    )
    .reset_index(drop=True)
)

df["factor_capitalizacion"] = (
    1
    + df["tasa_mensual"]
)

df["vf_nominal"] = (
    df
    .groupby(
        "entidad"
    )[
        "factor_capitalizacion"
    ]
    .cumprod()
    * CAPITAL_INICIAL
)

IPC_BASE = (
    df_ipc.loc[
        df_ipc["periodo"]
        == pd.Timestamp("2018-01-31"),
        "ipc"
    ]
    .iloc[0]
)

df["vf_real"] = (
    df["vf_nominal"]
    *
    (
        IPC_BASE
        /
        df["ipc"]
    )
)

# ============================================================
# BASE FINAL
# ============================================================

df_final = (
    df[
        [
            "periodo",
            "fecha_sbs",
            "entidad",
            "tasa_pasiva",
            "ipc",
            "tasa_mensual_pct",
            "vf_nominal",
            "vf_real"
        ]
    ]
    .sort_values(
        [
            "periodo",
            "entidad"
        ]
    )
    .reset_index(drop=True)
)

# ============================================================
# VALIDACIONES
# ============================================================

if df_final.isna().sum().sum() != 0:

    raise ValueError(
        "Existen faltantes en datos_procesados."
    )

if (
    df_final
    .duplicated(
        subset=[
            "periodo",
            "entidad"
        ]
    )
    .sum()
    != 0
):

    raise ValueError(
        "Existen duplicados."
    )

if len(df_final) < 1000:

    raise ValueError(
        "La base tiene menos de 1000 filas."
    )

# ============================================================
# GUARDAR
# ============================================================

df_final.to_csv(
    ARCHIVO_FINAL,
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# HASH
# ============================================================

sha256 = hashlib.sha256()

with open(
    ARCHIVO_FINAL,
    "rb"
) as archivo:

    for bloque in iter(
        lambda: archivo.read(8192),
        b""
    ):

        sha256.update(
            bloque
        )

hash_final = sha256.hexdigest()

# ============================================================
# LOG
# ============================================================

with open(
    LOG,
    "a",
    encoding="utf-8"
) as log:

    log.write("\n" + "=" * 70 + "\n")
    log.write("03_limpieza_datos.py\n")
    log.write("=" * 70 + "\n")

    log.write(
        f"Fecha y hora: {datetime.now()}\n"
    )

    log.write(
        f"Entidades completas: "
        f"{df_final['entidad'].nunique()}\n"
    )

    log.write(
        f"Periodos: "
        f"{df_final['periodo'].nunique()}\n"
    )

    log.write(
        f"Filas procesadas: {len(df_final)}\n"
    )

    log.write(
        f"Faltantes finales: "
        f"{df_final.isna().sum().sum()}\n"
    )

    log.write(
        f"Outliers IQR detectados "
        f"y conservados: {n_outliers}\n"
    )

    log.write(
        "Interpolaciones: 0\n"
    )

    log.write(
        f"SHA-256: {hash_final}\n"
    )

print("=" * 70)
print("LIMPIEZA COMPLETADA")
print("=" * 70)

print(
    "Filas:",
    len(df_final)
)

print(
    "Entidades:",
    df_final["entidad"].nunique()
)

print(
    "Periodos:",
    df_final["periodo"].nunique()
)

print(
    "Outliers IQR identificados y conservados:",
    n_outliers
)

print(
    "SHA-256:",
    hash_final
)

print(
    "Archivo:",
    ARCHIVO_FINAL
)
