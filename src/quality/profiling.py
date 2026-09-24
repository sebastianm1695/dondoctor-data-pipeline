import json
import pandas as pd

def perfilar_todas_las_columnas(df: pd.DataFrame, nombre_fuente: str) -> pd.DataFrame:
    """Genera perfilamiento exhaustivo columna por columna sin fallar por tipos anidados."""
    metricas = []
    total_filas = len(df)

    for col in df.columns:
        nulos_cant = int(df[col].isnull().sum())
        nulos_pct = round((nulos_cant / total_filas) * 100, 2)
        
        # Conversión segura a string para dicts y listas de JSON
        serie_str = df[col].apply(
            lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) 
            else (str(x) if pd.notnull(x) else None)
        )
        
        valores_unicos = int(serie_str.nunique(dropna=True))
        ejemplos = list(serie_str.dropna().unique()[:3])

        metricas.append({
            "fuente": nombre_fuente,
            "columna": col,
            "tipo_dato": str(df[col].dtype),
            "total_registros": total_filas,
            "nulos_cantidad": nulos_cant,
            "nulos_porcentaje": f"{nulos_pct}%",
            "completitud_porcentaje": f"{round(100 - nulos_pct, 2)}%",
            "valores_unicos": valores_unicos,
            "ejemplos_valores": ejemplos
        })

    return pd.DataFrame(metricas)