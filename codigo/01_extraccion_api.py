# Nombres y apellidos: Huaroc Cardenas Jordan Jose
# Código de matrícula: 2024200503I
# Tema N.º 20: Capitalización compuesta frente a la inflación: poder adquisitivo del ahorro peruano
# Fecha de extracción: 2026-09-25

import os
import html
import requests
import pandas as pd

from io import StringIO
from datetime import datetime

# ============================================================
# PARÁMETROS CONGELADOS
# ============================================================

FECHA_INICIO = "2018-1"
FECHA_CORTE = "2026-8"

SERIE_IPC = "PN38705PM"

URL_BCRP = (
    "https://estadisticas.bcrp.gob.pe/"
    "estadisticas/series/api/"
    f"{SERIE_IPC}/csv/"
    f"{FECHA_INICIO}/{FECHA_CORTE}/esp"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; FinanzasI-UNCP/1.0; uso-academico)"
    )
}

# ============================================================
# RUTAS RELATIVAS
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

os.makedirs(
    RUTA_CRUDOS,
    exist_ok=True
)

ARCHIVO_CRUDO = os.path.join(
    RUTA_CRUDOS,
    "ipc_bcrp_PN38705PM_2024200503I.csv"
)

LOG = os.path.join(
    BASE_DIR,
    "log_ejecucion.txt"
)

# ============================================================
# EXTRACCIÓN
# ============================================================

inicio = datetime.now()

respuesta = requests.get(
    URL_BCRP,
    headers=HEADERS,
    timeout=30
)

respuesta.raise_for_status()

# Guardar exactamente los bytes recibidos.
with open(
    ARCHIVO_CRUDO,
    "wb"
) as archivo:

    archivo.write(
        respuesta.content
    )

# ============================================================
# CONTAR FILAS SIN MODIFICAR EL ARCHIVO CRUDO
# ============================================================

texto = respuesta.content.decode(
    "utf-8-sig",
    errors="replace"
)

texto_parseo = (
    texto
    .replace("<br>", "\n")
    .replace("<br/>", "\n")
    .replace("<br />", "\n")
)

texto_parseo = html.unescape(
    texto_parseo
)

df_control = pd.read_csv(
    StringIO(texto_parseo)
)

filas = len(df_control)

fin = datetime.now()

# ============================================================
# LOG
# ============================================================

with open(
    LOG,
    "a",
    encoding="utf-8"
) as log:

    log.write("\n" + "=" * 70 + "\n")
    log.write("01_extraccion_api.py\n")
    log.write("=" * 70 + "\n")

    log.write(
        f"Fecha y hora: {fin}\n"
    )

    log.write(
        f"Endpoint: {URL_BCRP}\n"
    )

    log.write(
        f"Código HTTP: {respuesta.status_code}\n"
    )

    log.write(
        f"Filas descargadas: {filas}\n"
    )

    log.write(
        f"Bytes descargados: {len(respuesta.content)}\n"
    )

    log.write(
        f"Archivo crudo: {ARCHIVO_CRUDO}\n"
    )

print("=" * 70)
print("EXTRACCIÓN API BCRP COMPLETADA")
print("=" * 70)

print("HTTP:", respuesta.status_code)
print("Filas:", filas)
print("Bytes:", len(respuesta.content))
print("Archivo:", ARCHIVO_CRUDO)
