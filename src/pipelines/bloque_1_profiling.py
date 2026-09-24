import os
import sys
import json
import pandas as pd

# Ajuste automático del PYTHONPATH a la raíz del proyecto
DIR_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

from src.utils.logger import obtener_logger
from src.quality.profiling import perfilar_todas_las_columnas

logger = obtener_logger("Bloque1_Profiling")
RUTA_RAW = os.path.join(DIR_RAIZ, "data", "raw")

def ejecutar_bloque_1():
    logger.info("Iniciando ejecución del Bloque 1 - Perfilamiento de Datos...")
    
    # Lectura de datasets
    try:
        df_norte = pd.read_csv(os.path.join(RUTA_RAW, "ips_norte_citas.csv"))
        df_sur = pd.read_csv(os.path.join(RUTA_RAW, "ips_sur_citas.csv"))
        df_occ = pd.read_csv(os.path.join(RUTA_RAW, "ips_occidente_citas.csv"), sep=";")
        
        eventos_wa = []
        with open(os.path.join(RUTA_RAW, "whatsapp_eventos.jsonl"), "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    eventos_wa.append(json.loads(line.strip()))
        df_wa = pd.DataFrame(eventos_wa)
    except FileNotFoundError as e:
        logger.error(f"Error al cargar datos. Verifica la carpeta 'data/raw/'. Detalle: {e}")
        return

    # Generación de perfilamiento
    prof_norte = perfilar_todas_las_columnas(df_norte, "IPS Norte")
    prof_sur = perfilar_todas_las_columnas(df_sur, "IPS Sur")
    prof_occ = perfilar_todas_las_columnas(df_occ, "IPS Occidente")
    prof_wa = perfilar_todas_las_columnas(df_wa, "WhatsApp Eventos")

    # Impresión completa de todas las fuentes
    print("\n" + "="*80)
    print(" RESUMEN DE PERFILAMIENTO - IPS NORTE ")
    print("="*80)
    print(prof_norte.to_string(index=False))

    print("\n" + "="*80)
    print(" RESUMEN DE PERFILAMIENTO - IPS SUR ")
    print("="*80)
    print(prof_sur.to_string(index=False))

    print("\n" + "="*80)
    print(" RESUMEN DE PERFILAMIENTO - IPS OCCIDENTE ")
    print("="*80)
    print(prof_occ.to_string(index=False))

    print("\n" + "="*80)
    print(" RESUMEN DE PERFILAMIENTO - WHATSAPP EVENTOS ")
    print("="*80)
    print(prof_wa.to_string(index=False))

if __name__ == "__main__":
    ejecutar_bloque_1()