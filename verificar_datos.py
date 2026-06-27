# ============================================================
#  BioCare Dashboard - Script de verificación de datos
#  Paso 2: comprobar que los datos se leen correctamente
# ============================================================

import pandas as pd

print("=" * 55)
print("  VERIFICACIÓN DE DATOS - BioCare Dashboard")
print("=" * 55)

# Leer los dos archivos de datos
equipos = pd.read_csv("equipos_biocare.csv")
historial = pd.read_csv("historial_mantenimiento_biocare.csv")

# Mostrar resumen de equipos
print(f"\n✓ Archivo de equipos cargado correctamente")
print(f"  - Total de equipos: {len(equipos)}")
print(f"  - Columnas: {', '.join(equipos.columns)}")

# Mostrar resumen del historial
print(f"\n✓ Archivo de historial cargado correctamente")
print(f"  - Total de registros: {len(historial)}")
preventivos = (historial['tipo_mantenimiento'] == 'Preventivo').sum()
correctivos = (historial['tipo_mantenimiento'] == 'Correctivo').sum()
print(f"  - Preventivos: {preventivos}")
print(f"  - Correctivos: {correctivos}")

# Mostrar los primeros 3 equipos
print(f"\n✓ Primeros 3 equipos de la lista:")
for _, eq in equipos.head(3).iterrows():
    print(f"  {eq['codigo']} - {eq['nombre']} (criticidad {eq['nivel_crit']})")

print("\n" + "=" * 55)
print("  ¡TODO FUNCIONA! Los datos están listos.")
print("=" * 55)
