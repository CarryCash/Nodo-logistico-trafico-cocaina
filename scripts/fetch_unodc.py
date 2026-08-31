
import os
import csv
import requests
from datetime import datetime

OUTPUT_CSV = "data/unodc_seizures.csv"

# Países de interés: Ecuador (origen/tránsito) y los principales
# destinos europeos reportados en informes UNODC/Europol
COUNTRIES = {
    "Ecuador": "ECU",
    "Belgica": "BEL",
    "PaisesBajos": "NLD",
    "Espana": "ESP",
}

# Endpoint SDMX de UNODC para incautaciones de drogas (dataset DF_DRUG_SEIZURES)
BASE_URL = "https://api.dataunodc.org/rest/data/dataunodc.un.org,DF_DRUG_SEIZURES,1.0"


def fetch_country_seizures(iso3: str):
    url = f"{BASE_URL}/A.{iso3}.COCAINE._T?format=jsondata"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_and_append(raw_json: dict, country_name: str):
    file_exists = os.path.isfile(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "fecha_descarga", "pais", "anio", "cantidad_kg_reportada"
            ])

        try:
            series_list = raw_json["data"]["dataSets"][0]["series"]
            structure = raw_json["data"]["structure"]["dimensions"]["observation"]
            time_periods = structure[0]["values"]

            for series_key, series_val in series_list.items():
                observations = series_val.get("observations", {})
                for obs_index, obs_val in observations.items():
                    year = time_periods[int(obs_index)]["id"]
                    value = obs_val[0]
                    writer.writerow([
                        datetime.utcnow().isoformat(),
                        country_name,
                        year,
                        value,
                    ])
        except (KeyError, IndexError) as e:
            print(f"No se pudo parsear respuesta de UNODC para {country_name}: {e}")


def main():
    for name, iso3 in COUNTRIES.items():
        try:
            raw = fetch_country_seizures(iso3)
            parse_and_append(raw, name)
            print(f"OK: datos de incautaciones actualizados para {name}")
        except Exception as e:
            print(f"ERROR descargando UNODC para {name}: {e}")


if __name__ == "__main__":
    main()
