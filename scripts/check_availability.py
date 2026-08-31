"""
check_availability.py
-----------------------
Script de diagnóstico (no se usa en el pipeline automático).
Consulta el endpoint de disponibilidad de datos de Comtrade para saber
qué períodos (meses/años) ya están publicados para Ecuador como reportero,
en vez de adivinar con fechas fijas.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("COMTRADE_API_KEY", "")

url = "https://comtradeapi.un.org/data/v1/getDA/C/M/HS"
params = {
    "reporterCode": "218",  # Ecuador
    "cmdCode": "0803",
    "flowCode": "X",
    "subscription-key": API_KEY,
}

import json

resp = requests.get(url, params=params, timeout=30)
print("Status:", resp.status_code)

data = resp.json().get("data", [])
if data:
    periods = sorted(row["period"] for row in data)
    print(f"Total de períodos disponibles: {len(periods)}")
    print(f"Más antiguo: {periods[0]}")
    print(f"Más reciente: {periods[-1]}")
else:
    print("No se encontraron períodos.")
    print(resp.text[:1000])