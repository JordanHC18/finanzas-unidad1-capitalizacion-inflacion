
# Finanzas I — Unidad I

## Tema

Capitalización compuesta frente a la inflación: poder adquisitivo del ahorro peruano

## Autor

Huaroc Cardenas Jordan Jose

Código de matrícula:

2024200503I

---

## Periodo de estudio

FECHA_INICIO = 2018-01-01

FECHA_CORTE = 2026-08-31

Frecuencia: mensual.

Periodos: 104.

---

## Fuentes

### SBS

Variable:
Tasa pasiva anual de depósitos de ahorro en moneda nacional
por entidad bancaria.

Portal:
https://www.sbs.gob.pe/app/pp/EstadisticasSAEEPortal/Paginas/TIPasivaDepositoEmpresa.aspx?tip=B

Vía:
web scraping programático.

### BCRPData

Serie:
PN38705PM

Variable:
IPC de Lima Metropolitana,
base diciembre de 2021 = 100.

Endpoint:
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN38705PM/csv/2018-1/2026-8/esp

Vía:
API.

---

## Base analítica

Observaciones finales:
1144

Entidades:
11

Periodos:
104

Columnas:
8

El panel utiliza únicamente entidades con información completa
durante los 104 periodos.

No se utilizaron interpolaciones en la tasa pasiva del panel final.

Los datos incompletos permanecen intactos en /datos_crudos.

---

## Variables principales

Variable endógena:

- vf_real

Variables exógenas:

- tasa_pasiva
- ipc
- vf_nominal

Variable auxiliar:

- tasa_mensual_pct

---

## Capitalización

Capital inicial de referencia:

S/ 1000.00

La tasa pasiva anual se transforma en tasa mensual equivalente.

El valor futuro nominal se calcula mediante capitalización compuesta.

El valor futuro real se obtiene deflactando el valor futuro nominal
con el IPC.

Periodo base del valor real:

enero de 2018.

---

## Orden de ejecución

1. 01_extraccion_api.py
2. 02_scraping_web.py
3. 03_limpieza_datos.py
4. 04_analisis.py

---

## Archivo procesado

datos_procesados_2024200503I.csv

SHA-256:

9b2224512144585c01db24d757652ae7b9a73b3fbeaa1dd76163e379e9f2ba7c

---

## Dependencias

Ver:

requirements.txt

---

## Variables de entorno

El proyecto no utiliza claves privadas.

Ver:

.env.example

---

## Repositorio GitHub

PENDIENTE_COLOCAR_URL_GITHUB


---

## Entorno de ejecución

Versión de Python: Python 3.13.15

Librerías utilizadas:

pandas==2.2.3
numpy==2.1.3
requests==2.32.4
beautifulsoup4==4.13.5
lxml==6.1.2
openpyxl==3.1.5
