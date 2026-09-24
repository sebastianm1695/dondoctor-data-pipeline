import os
import sys
import json
import pandas as pd

# Ajuste automático del PYTHONPATH a la raíz del proyecto
DIR_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

from src.utils.logger import obtener_logger
from src.utils.hashing import anonimizar_pii

logger = obtener_logger("Bloque2_Transformation")
RUTA_RAW = os.path.join(DIR_RAIZ, "data", "raw")
RUTA_PROCESSED = os.path.join(DIR_RAIZ, "data", "processed")

def ejecutar_bloque_2():
    logger.info("Iniciando ejecución del Bloque 2 - Transformaciones y Capa Silver...")
    os.makedirs(RUTA_PROCESSED, exist_ok=True)

    try:
        # 1. Cargar datasets de las IPS
        df_norte = pd.read_csv(os.path.join(RUTA_RAW, "ips_norte_citas.csv"))
        df_sur = pd.read_csv(os.path.join(RUTA_RAW, "ips_sur_citas.csv"))
        df_occ = pd.read_csv(os.path.join(RUTA_RAW, "ips_occidente_citas.csv"), sep=";")

        # Asignar origen a cada dataset
        df_norte["ips_origen"] = "IPS Norte"
        df_sur["ips_origen"] = "IPS Sur"
        df_occ["ips_origen"] = "IPS Occidente"

        # 2. Unificar esquemas y estandarizar columnas
        # Unificación de dataframes de citas
        df_citas = pd.concat([df_norte, df_sur, df_occ], ignore_index=True)

        # 3. Aplicar anonimización de PII en la columna de documento si existe
        cols_pii = [col for col in df_citas.columns if "paciente" in col.lower() or "doc" in col.lower() or "cedula" in col.lower()]
        for col in cols_pii:
            df_citas[f"{col}_hashed"] = df_citas[col].astype(str).apply(anonimizar_pii)

        # 4. Procesar eventos de WhatsApp (JSONL)
        eventos_wa = []
        with open(os.path.join(RUTA_RAW, "whatsapp_eventos.jsonl"), "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    eventos_wa.append(json.loads(line.strip()))
        df_wa = pd.DataFrame(eventos_wa)

        # Anonimizar teléfonos en WhatsApp
        if "telefono" in df_wa.columns:
            df_wa["telefono_hashed"] = df_wa["telefono"].astype(str).apply(anonimizar_pii)

        # 5. Guardar archivos limpios en data/processed/
        ruta_citas_out = os.path.join(RUTA_PROCESSED, "citas_unificadas_silver.csv")
        ruta_wa_out = os.path.join(RUTA_PROCESSED, "whatsapp_eventos_silver.csv")

        df_citas.to_csv(ruta_citas_out, index=False, encoding="utf-8")
        df_wa.to_csv(ruta_wa_out, index=False, encoding="utf-8")

        logger.info(f"Citas procesadas guardadas en: {ruta_citas_out}")
        logger.info(f"Eventos WhatsApp guardados en: {ruta_wa_out}")
        logger.info("Procesamiento del Bloque 2 completado con éxito.")

    except Exception as e:
        logger.error(f"Error durante la transformación: {str(e)}")

if __name__ == "__main__":
    ejecutar_bloque_2()