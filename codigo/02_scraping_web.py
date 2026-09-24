# Nombres y apellidos: Huaroc Cardenas Jordan Jose
# Código de matrícula: 2024200503I
# Tema N.º 20: Capitalización compuesta frente a la inflación: poder adquisitivo del ahorro peruano
# Fecha de extracción: 2026-09-24

import os
import json
import time
import requests
import pandas as pd

from bs4 import BeautifulSoup
from io import StringIO
from datetime import datetime

# ============================================================
# PARÁMETROS CONGELADOS
# ============================================================

FECHA_INICIO = "2018-01-01"
FECHA_CORTE = "2026-08-31"

URL_SBS = (
    "https://www.sbs.gob.pe/app/pp/"
    "EstadisticasSAEEPortal/Paginas/"
    "TIPasivaDepositoEmpresa.aspx?tip=B"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; FinanzasI-UNCP/1.0; uso-academico)"
    ),
    "Referer": URL_SBS
}

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

os.makedirs(
    RUTA_HTML,
    exist_ok=True
)

LOG_GENERAL = os.path.join(
    BASE_DIR,
    "log_ejecucion.txt"
)

LOG_CSV = os.path.join(
    RUTA_CRUDOS,
    "log_sbs_2024200503I.csv"
)

# ============================================================
# CONSULTAR UNA FECHA EXACTA
# ============================================================

def consultar_fecha(fecha):

    fecha = pd.Timestamp(fecha)

    fecha_iso = fecha.strftime("%Y-%m-%d")
    fecha_visual = fecha.strftime("%d/%m/%Y")
    fecha_telerik = fecha.strftime(
        "%Y-%m-%d-00-00-00"
    )

    sesion = requests.Session()
    sesion.headers.update(HEADERS)

    inicial = sesion.get(
        URL_SBS,
        timeout=30
    )

    inicial.raise_for_status()

    soup = BeautifulSoup(
        inicial.text,
        "html.parser"
    )

    datos_post = {}

    for campo in soup.find_all("input"):

        nombre = campo.get("name")

        if (
            nombre
            and campo.get("type") == "hidden"
        ):

            datos_post[nombre] = (
                campo.get("value", "")
            )

    datos_post[
        "ctl00$cphContent$rdpDate"
    ] = fecha_iso

    datos_post[
        "ctl00$cphContent$rdpDate$dateInput"
    ] = fecha_visual

    estado_fecha = {
        "enabled": True,
        "emptyMessage": "",
        "validationText": fecha_telerik,
        "valueAsString": fecha_telerik,
        "minDateStr": "1000-01-01-00-00-00",
        "maxDateStr": "2099-12-30-00-00-00",
        "lastSetTextBoxValue": fecha_visual
    }

    datos_post[
        "ctl00_cphContent_rdpDate_"
        "dateInput_ClientState"
    ] = json.dumps(
        estado_fecha,
        separators=(",", ":")
    )

    datos_post[
        "ctl00_cphContent_rdpDate_calendar_AD"
    ] = (
        f"[[1000,1,1],"
        f"[2099,12,30],"
        f"[{fecha.year},{fecha.month},{fecha.day}]]"
    )

    datos_post[
        "ctl00$cphContent$btnConsultar"
    ] = "Consultar"

    datos_post.pop(
        "ctl00$cphContent$btnExportar",
        None
    )

    datos_post["__EVENTTARGET"] = ""
    datos_post["__EVENTARGUMENT"] = ""

    # Rúbrica: mínimo 1 segundo entre solicitudes.
    time.sleep(1.2)

    respuesta = sesion.post(
        URL_SBS,
        data=datos_post,
        timeout=30
    )

    respuesta.raise_for_status()

    soup_final = BeautifulSoup(
        respuesta.text,
        "html.parser"
    )

    campo_fecha = soup_final.find(
        "input",
        attrs={
            "name":
            "ctl00$cphContent$rdpDate"
        }
    )

    if campo_fecha is None:

        raise ValueError(
            "No se pudo verificar la fecha."
        )

    if campo_fecha.get("value") != fecha_iso:

        raise ValueError(
            "La SBS devolvió una fecha diferente."
        )

    return respuesta


# ============================================================
# DETECTAR SI EXISTE TABLA BANCARIA
# ============================================================

def tiene_tabla_bancaria(html):

    tablas = pd.read_html(
        StringIO(html)
    )

    for tabla in tablas:

        texto = (
            " ".join(
                str(c)
                for c in tabla.columns
            )
            + " "
            + tabla.astype(str).to_string()
        ).lower()

        bancos = sum(
            1
            for banco in BANCOS_CLAVE
            if banco.lower() in texto
        )

        if (
            bancos >= 4
            and "ahorro" in texto
        ):
            return True

    return False


# ============================================================
# BUSCAR ÚLTIMA FECHA DISPONIBLE DEL MES
# ============================================================

def extraer_mes(
    fecha_objetivo,
    max_retroceso=7
):

    fecha_objetivo = pd.Timestamp(
        fecha_objetivo
    )

    errores = []

    for retroceso in range(
        max_retroceso + 1
    ):

        fecha_sbs = (
            fecha_objetivo
            - pd.Timedelta(days=retroceso)
        )

        if (
            fecha_sbs.month
            != fecha_objetivo.month
        ):
            break

        try:

            respuesta = consultar_fecha(
                fecha_sbs
            )

            if not tiene_tabla_bancaria(
                respuesta.text
            ):

                errores.append(
                    f"{fecha_sbs.date()}: "
                    "sin tabla bancaria"
                )

                continue

            nombre = (
                "sbs_"
                + fecha_sbs.strftime(
                    "%Y_%m_%d"
                )
                + ".html"
            )

            ruta = os.path.join(
                RUTA_HTML,
                nombre
            )

            # Guardar respuesta original íntegra.
            with open(
                ruta,
                "wb"
            ) as archivo:

                archivo.write(
                    respuesta.content
                )

            return {
                "periodo":
                    fecha_objetivo.strftime(
                        "%Y-%m-%d"
                    ),
                "fecha_sbs":
                    fecha_sbs.strftime(
                        "%Y-%m-%d"
                    ),
                "retroceso_dias":
                    retroceso,
                "http":
                    respuesta.status_code,
                "bytes":
                    len(respuesta.content),
                "archivo":
                    nombre,
                "error":
                    ""
            }

        except Exception as error:

            errores.append(
                f"{fecha_sbs.date()}: {error}"
            )

    raise ValueError(
        " | ".join(errores)
    )


# ============================================================
# EJECUCIÓN
# ============================================================

fechas = pd.date_range(
    start=FECHA_INICIO,
    end=FECHA_CORTE,
    freq="ME"
)

registros = []

inicio = datetime.now()

for numero, fecha in enumerate(
    fechas,
    start=1
):

    print(
        f"[{numero}/{len(fechas)}] "
        f"{fecha.strftime('%Y-%m')}",
        end=" "
    )

    try:

        info = extraer_mes(
            fecha
        )

        registros.append(info)

        print(
            "OK | fecha SBS:",
            info["fecha_sbs"]
        )

    except Exception as error:

        print(
            "ERROR:",
            error
        )

        registros.append({
            "periodo":
                fecha.strftime("%Y-%m-%d"),
            "fecha_sbs":
                "",
            "retroceso_dias":
                "",
            "http":
                "",
            "bytes":
                "",
            "archivo":
                "",
            "error":
                str(error)
        })

df_log = pd.DataFrame(
    registros
)

df_log.to_csv(
    LOG_CSV,
    index=False,
    encoding="utf-8-sig"
)

fin = datetime.now()

exitosos = (
    df_log["error"]
    .eq("")
    .sum()
)

with open(
    LOG_GENERAL,
    "a",
    encoding="utf-8"
) as log:

    log.write("\n" + "=" * 70 + "\n")
    log.write("02_scraping_web.py\n")
    log.write("=" * 70 + "\n")

    log.write(
        f"Fecha y hora: {fin}\n"
    )

    log.write(
        f"Periodos solicitados: {len(fechas)}\n"
    )

    log.write(
        f"Periodos descargados: {exitosos}\n"
    )

    log.write(
        f"HTTP exitosos: {exitosos}\n"
    )

print()
print("=" * 70)
print("SCRAPING SBS TERMINADO")
print("=" * 70)

print(
    "Periodos descargados:",
    exitosos
)

print(
    "Directorio crudo:",
    RUTA_HTML
)
