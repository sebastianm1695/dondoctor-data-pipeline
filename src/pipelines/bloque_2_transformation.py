import os
import json
import pandas as pd
from src.utils.hashing import anonimizar_pii
from src.utils.logger import obtener_logger

logger = obtener_logger("Bloque2_Transformation")

PATH_RAW = "data/raw"
PATH_PROCESSED = "data/processed"

def transformar_ips_norte():
    file_path = os.path.join(PATH_RAW, "ips_norte_citas.csv")
    df = pd.read_csv(file_path)
    df["ips_origen"] = "NORTE"
    df = df.drop_duplicates(subset=["cita_id", "ips_origen"])
    return df

def transformar_ips_sur():
    file_path = os.path.join(PATH_RAW, "ips_sur_citas.csv")
    df = pd.read_csv(file_path)
    df["ips_origen"] = "SUR"
    
    # Anonimización criptográfica estricta de PII expuesta
    df["documento_identidad"] = df["documento_identidad"].astype(str).apply(anonimizar_pii)
    df["telefono"] = df["telefono"].astype(str).apply(anonimizar_pii)
    
    df = df.drop_duplicates(subset=["cita_id", "ips_origen"])
    return df

def transformar_ips_occidente():
    file_path = os.path.join(PATH_RAW, "ips_occidente_citas.csv")
    
    # Lectura robusta manejando delimitador punto y coma (;)
    try:
        df = pd.read_csv(file_path, sep=";")
        if df.shape[1] == 1:
            df = pd.read_csv(file_path, sep=None, engine="python")
    except Exception:
        df = pd.read_csv(file_path, sep=",", on_bad_lines="skip")
    
    # Homologación de esquema y nombres de columnas
    mapeo_columnas = {
        "id_cita": "cita_id",
        "id_paciente": "paciente_id",
        "edad_paciente": "edad",
        "genero": "sexo",
        "regimen_salud": "regimen",
        "fecha_hora_cita": "fecha_cita",
        "estado_cita": "estado",
        "id_cita_origen": "cita_origen_id"
    }
    df = df.rename(columns=mapeo_columnas)
    
    # Homologación de dominios (Estados)
    mapeo_estados = {
        "ATD": "ATENDIDA",
        "CAN": "CANCELADA",
        "NAS": "NO_ASISTIO",
        "PEND": "PENDIENTE",
        "REAG": "REAGENDADA"
    }
    df["estado"] = df["estado"].replace(mapeo_estados)
    
    # Homologación de género / sexo
    mapeo_sexo = {"Femenino": "F", "Masculino": "M"}
    df["sexo"] = df["sexo"].replace(mapeo_sexo)
    
    # Limpieza de fechas (remover formato ISO 'T')
    for col_fecha in ["fecha_creacion", "fecha_cita", "fecha_actualizacion"]:
        if col_fecha in df.columns:
            df[col_fecha] = df[col_fecha].astype(str).str.replace("T", " ")
            
    df["ips_origen"] = "OCCIDENTE"
    df = df.drop_duplicates(subset=["cita_id", "ips_origen"])
    return df

def transformar_whatsapp():
    file_path = os.path.join(PATH_RAW, "whatsapp_eventos.jsonl")
    registros = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            mensaje_obj = json.loads(data.get("mensaje", "{}")) if isinstance(data.get("mensaje"), str) else data.get("mensaje", {})
            contexto_obj = json.loads(data.get("contexto", "{}")) if isinstance(data.get("contexto"), str) else data.get("contexto", {})
            
            destinatario_raw = mensaje_obj.get("destinatario", "")
            destinatario_hash = anonimizar_pii(destinatario_raw) if destinatario_raw else None
            
            registros.append({
                "evento_id": data.get("_id"),
                "timestamp_ms": data.get("ts"),
                "tipo_evento": data.get("tipo"),
                "destinatario_hash": destinatario_hash,
                "plantilla": mensaje_obj.get("plantilla"),
                "ips": contexto_obj.get("ips"),
                "ref_cita": contexto_obj.get("ref_cita")
            })
            
    df_wa = pd.DataFrame(registros)
    df_wa = df_wa.drop_duplicates(subset=["evento_id"])
    return df_wa

def ejecutar_pipeline_transformacion():
    os.makedirs(PATH_PROCESSED, exist_ok=True)
    logger.info("Iniciando pipeline de transformación y unificación para la capa Silver...")
    
    df_norte = transformar_ips_norte()
    df_sur = transformar_ips_sur()
    df_occidente = transformar_ips_occidente()
    
    # Unificación consolidada de citas
    df_citas_silver = pd.concat([df_norte, df_sur, df_occidente], ignore_index=True)
    path_citas_out = os.path.join(PATH_PROCESSED, "citas_unificadas_silver.csv")
    df_citas_silver.to_csv(path_citas_out, index=False)
    logger.info(f"Citas unificadas guardadas en: {path_citas_out} ({len(df_citas_silver)} registros)")
    
    # Procesamiento de WhatsApp
    df_wa_silver = transformar_whatsapp()
    path_wa_out = os.path.join(PATH_PROCESSED, "whatsapp_eventos_silver.csv")
    df_wa_silver.to_csv(path_wa_out, index=False)
    logger.info(f"Eventos de WhatsApp guardados en: {path_wa_out} ({len(df_wa_silver)} registros)")

if __name__ == "__main__":
    ejecutar_pipeline_transformacion()