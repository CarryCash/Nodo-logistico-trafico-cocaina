"""
fetch_comtrade.py
------------------
Descarga volumen mensual de exportaciones de Ecuador hacia puertos europeos
clave (Belgica, Paises Bajos, Espana) usando la API publica de UN Comtrade.

Rango de interes: 2024-01 hasta el periodo mas reciente ya publicado.

Por que estos paises: Amberes (Belgica) y Rotterdam (Paises Bajos) son los
puertos europeos con mas incautaciones de cocaina ligadas a contenedores
provenientes de Sudamerica, segun reportes anuales de UNODC y Europol.

API: https://comtradeapi.un.org
Registro gratuito de API key: https://comtradedeveloper.un.org/
"""

import os
import csv
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Configuracion ---
API_KEY = os.environ.get("COMTRADE_API_KEY", "")
REPORTER = "218"  # codigo Comtrade de Ecuador

# Mapa codigo de pais -> nombre legible
PARTNER_NAMES = {
    "056": "Belgica",
    "528": "PaisesBajos",
    "724": "Espana",
}

# Codigo HS 08 = frutas (banano fresco es el disfraz mas comun reportado
# para contenedores con cocaina hacia Europa)
COMMODITY_CODE = "0803"

OUTPUT_CSV = "data/comtrade_ecuador_exports.csv"

RANGE_START = "202401"  # nos enfocamos desde enero 2024


def get_available_periods() -> list:
    """Consulta que periodos mensuales ya estan publicados para Ecuador."""
    url = "https://comtradeapi.un.org/data/v1/getDA/C/M/HS"
    params = {
        "reporterCode": REPORTER,
        "cmdCode": COMMODITY_CODE,
        "flowCode": "X",
        "subscription-key": API_KEY,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    periods = sorted(str(row["period"]) for row in data)
    return [p for p in periods if p >= RANGE_START]


def get_already_downloaded_periods() -> set:
    """Lee el CSV existente para no volver a pedir periodos ya guardados."""
    if not os.path.isfile(OUTPUT_CSV):
        return set()
    downloaded = set()
    with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            downloaded.add(str(row["periodo"]))
    return downloaded


def fetch_period_data(period: str, retries: int = 3):
    """
    Trae TODOS los socios comerciales para un periodo en una sola llamada
    (sin partnerCode en la URL), y luego filtramos en codigo.
    """
    url = "https://comtradeapi.un.org/data/v1/get/C/M/HS"
    params = {
        "reporterCode": REPORTER,
        "period": period,
        "cmdCode": COMMODITY_CODE,
        "flowCode": "X",
        "subscription-key": API_KEY,
    }

    for attempt in range(1, retries + 1):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            wait = 15 * attempt
            print(f"  Limite de requests alcanzado, esperando {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json().get("data", [])

    print(f"  Se agotaron los reintentos para el periodo {period}.")
    return []


def append_to_csv(rows: list):
    file_exists = os.path.isfile(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "fecha_descarga", "periodo", "socio_comercial",
                "codigo_producto", "valor_usd", "peso_neto_kg"
            ])
        for row in rows:
            partner_code = str(row.get("partnerCode"))
            partner_name = PARTNER_NAMES.get(partner_code)
            if not partner_name:
                continue  # no es uno de nuestros 3 paises de interes, se ignora
            writer.writerow([
                datetime.utcnow().isoformat(),
                row.get("period"),
                partner_name,
                row.get("cmdCode"),
                row.get("primaryValue"),
                row.get("netWgt"),
            ])


def main():
    if not API_KEY:
        print("ADVERTENCIA: no se encontro COMTRADE_API_KEY, se omite esta fuente.")
        return

    available = get_available_periods()
    already_have = get_already_downloaded_periods()
    pending = [p for p in available if p not in already_have]

    print(f"Periodos disponibles en el rango 2024+: {len(available)}")
    print(f"Ya descargados previamente: {len(already_have)}")
    print(f"Pendientes por descargar hoy: {len(pending)}")

    if not pending:
        print("Nada nuevo que descargar, ya estas al dia.")
        return

    for period in pending:
        try:
            data = fetch_period_data(period)
            if data:
                append_to_csv(data)
                print(f"OK: periodo {period} guardado")
            else:
                print(f"Sin datos para el periodo {period}")
        except Exception as e:
            print(f"ERROR en periodo {period}: {e}")

        time.sleep(6)  # pausa entre llamadas para respetar el limite gratuito


if __name__ == "__main__":
    main()