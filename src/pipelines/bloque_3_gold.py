import os
import pandas as pd
from src.utils.logger import obtener_logger

logger = obtener_logger("Bloque3_Gold")

PATH_PROCESSED = "data/processed"
PATH_GOLD = "data/gold"

def construir_capa_gold():
    os.makedirs(PATH_GOLD, exist_ok=True)
    logger.info("Iniciando construcción de la Capa Gold (Modelo Dimensional)...")
    
    # 1. Lectura de la capa Silver
    file_path = os.path.join(PATH_PROCESSED, "citas_unificadas_silver.csv")
    if not os.path.exists(file_path):
        logger.error(f"No se encontró el archivo en {file_path}. Ejecuta el Bloque 2 primero.")
        return
    
    df_citas = pd.read_csv(file_path)
    logger.info(f"Registros cargados desde Silver: {len(df_citas)}")
    
    # 2. Definición oficial de ausentismo (E2 / E4)
    # Ausentismo = 1 si la cita quedó en estado NO_ASISTIO, 0 en cualquier otro caso
    df_citas["es_ausentismo"] = (df_citas["estado"].str.upper() == "NO_ASISTIO").astype(int)
    
    # 3. Construcción del Modelo Dimensional (Esquema en Estrella)
    
    # Dimensión Paciente: basada exclusivamente en el paciente_hash unificado
    cols_paciente = [c for c in ["paciente_hash", "edad", "sexo", "regimen"] if c in df_citas.columns]
    if "paciente_hash" in df_citas.columns:
        dim_paciente = df_citas[cols_paciente].drop_duplicates(subset=["paciente_hash"]).reset_index(drop=True)
    else:
        dim_paciente = pd.DataFrame()
        
    # Dimensión IPS
    dim_ips = df_citas[["ips_origen"]].drop_duplicates().reset_index(drop=True)
    dim_ips["ips_id"] = dim_ips.index + 1
    
    # Dimensión Tiempo (extraída de la fecha de la cita)
    df_citas["fecha_cita"] = pd.to_datetime(df_citas["fecha_cita"], errors="coerce")
    df_citas["fecha_str"] = df_citas["fecha_cita"].dt.date
    dim_tiempo = df_citas[["fecha_str"]].dropna().drop_duplicates().reset_index(drop=True)
    dim_tiempo["anio"] = pd.to_datetime(dim_tiempo["fecha_str"]).dt.year
    dim_tiempo["mes"] = pd.to_datetime(dim_tiempo["fecha_str"]).dt.month
    dim_tiempo["dia_semana"] = pd.to_datetime(dim_tiempo["fecha_str"]).dt.day_name()
    
    # Tabla de Hechos: Fact_Citas
    cols_hechos = [c for c in ["cita_id", "paciente_hash", "ips_origen", "estado", "es_ausentismo", "fecha_cita"] if c in df_citas.columns]
    fact_citas = df_citas[cols_hechos].copy()
    
    # 4. Guardar en Capa Gold (Idempotencia garantizada por sobrescritura limpia)
    dim_paciente.to_csv(os.path.join(PATH_GOLD, "dim_paciente.csv"), index=False)
    dim_ips.to_csv(os.path.join(PATH_GOLD, "dim_ips.csv"), index=False)
    dim_tiempo.to_csv(os.path.join(PATH_GOLD, "dim_tiempo.csv"), index=False)
    fact_citas.to_csv(os.path.join(PATH_GOLD, "fact_citas.csv"), index=False)
    
    logger.info(f"Capa Gold generada con éxito en {PATH_GOLD}:")
    logger.info(f" - dim_paciente: {len(dim_paciente)} registros")
    logger.info(f" - dim_ips: {len(dim_ips)} registros")
    logger.info(f" - dim_tiempo: {len(dim_tiempo)} registros")
    logger.info(f" - fact_citas: {len(fact_citas)} registros")

if __name__ == "__main__":
    construir_capa_gold()