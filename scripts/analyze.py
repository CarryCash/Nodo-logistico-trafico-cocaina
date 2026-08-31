import pandas as pd
import os

COMTRADE_CSV = "data/comtrade_ecuador_exports.csv"
UNODC_CSV = "data/unodc_seizures.csv"
OUTPUT_REPORT = "data/analisis_correlacion.csv"


def main():
    if not (os.path.isfile(COMTRADE_CSV) and os.path.isfile(UNODC_CSV)):
        print("Aún no hay suficientes datos históricos para analizar. "
              "Deja que el workflow corra unas semanas más.")
        return

    trade = pd.read_csv(COMTRADE_CSV)
    seizures = pd.read_csv(UNODC_CSV)

    # Agregamos volumen de exportación por año y socio comercial
    trade["anio"] = trade["periodo"].astype(str).str[:4]
    trade_agg = trade.groupby(["anio", "socio_comercial"])["peso_neto_kg"] \
                      .sum().reset_index()

    # Unimos con incautaciones por año y país
    merged = trade_agg.merge(
        seizures,
        left_on=["anio", "socio_comercial"],
        right_on=["anio", "pais"],
        how="inner",
    )

    if merged.empty:
        print("No hay suficiente traslape de años/países todavía para correlacionar.")
        return

    correlation = merged["peso_neto_kg"].corr(
        merged["cantidad_kg_reportada"].astype(float)
    )

    merged.to_csv(OUTPUT_REPORT, index=False)
    print(f"Análisis guardado en {OUTPUT_REPORT}")
    print(f"Correlación exportaciones vs incautaciones: {correlation:.3f}")
    print("(Recuerda: correlación no implica causalidad. "
          "Sirve para generar hipótesis, no conclusiones definitivas.)")


if __name__ == "__main__":
    main()
