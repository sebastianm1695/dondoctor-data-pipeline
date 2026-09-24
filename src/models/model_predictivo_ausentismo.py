"""
========================================================================================
ENTREGABLE 5: MODELO PREDICTIVO DE AUSENTISMOS ("SMART REMINDERS" - ML CORE)
========================================================================================
Definición del Problema y Enfoque de Modelado:
- Tipo de Tarea: Clasificación binaria supervisada.
- Variable Objetivo (target): ausentismo (1 si el campo 'estado' es 'NO_ASISTIO'; 0 en caso contrario).
- Algoritmo Base Seleccionado: LightGBM (Gradient Boosting Decision Tree), debido a sus altas prestaciones con datos tabulares heterogéneos, manejo nativo de nulos y velocidad de entrenamiento sobre volúmenes masivos.

Ingeniería de Características (Feature Engineering):
- Variables Demográficas y de Contexto: edad, sexo, regimen, localidad, sede.
- Variables de la Cita y del Sistema: especialidad, medico_id, canal_agendamiento, antelación calculada entre fecha_creacion y fecha_cita.
- Variables de Operación: recordatorio_enviado, confirmada, gestion_recuperacion.

Estrategia de Validación y Entrenamiento:
- Validación Temporal (Time-Based Split): Entrenamiento con datos históricos y validación estricta basada en el orden cronológico para evitar data leakage.
- Métricas de Evaluación de Negocio: ROC-AUC para discriminación general, y Precision/Recall en la clase 1 (Ausentismo) para minimizar falsos positivos y maximizar captura de ausencias para sobreventa.
========================================================================================
"""

import os
import lightgbm as lgb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import LabelEncoder

# Definición de rutas estandarizadas del repositorio
PATH_PROCESSED = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))

def cargar_datos_procesados():
    """
    Carga los datos utilizando la ruta estandarizada y el nombre correcto de la capa Silver.
    """
    file_path = os.path.join(PATH_PROCESSED, "citas_unificadas_silver.csv")
    df = pd.read_csv(file_path)
    print(f"Datos cargados exitosamente desde: {file_path}")
    return df

def entrenar_y_evaluar_modelo():
    # 1. Ingesta directa usando la ruta estandarizada
    df = cargar_datos_procesados()
    
    # 2. Mapeo de la variable objetivo a partir del campo real 'estado' ('NO_ASISTIO')
    df['ausentismo'] = (df['estado'] == 'NO_ASISTIO').astype(int)
    
    # 3. Ingeniería de características temporales (Antelación en días, día de semana, hora)
    df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'])
    df['fecha_cita'] = pd.to_datetime(df['fecha_cita'])
    df['antelacion_dias'] = (df['fecha_cita'] - df['fecha_creacion']).dt.days.clip(lower=0)
    df['dia_semana'] = df['fecha_cita'].dt.dayofweek
    df['hora_cita'] = df['fecha_cita'].dt.hour

    # 4. Codificación de variables categóricas del esquema
    cat_cols = ['sexo', 'regimen', 'localidad', 'especialidad', 'medico_id', 'sede', 'canal_agendamiento', 'gestion_recuperacion']
    for col in cat_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))

    # 5. Definición de features (variables predictoras) y target
    features = [
        'edad', 'sexo', 'regimen', 'localidad', 'especialidad', 'medico_id', 'sede', 
        'canal_agendamiento', 'antelacion_dias', 'dia_semana', 'hora_cita',
        'recordatorio_enviado', 'confirmada', 'gestion_recuperacion'
    ]
    
    # Filtrar únicamente las columnas que existan en el DataFrame cargado
    features = [f for f in features if f in df.columns]
    target = 'ausentismo'
    
    X = df[features]
    y = df[target]
    
    # 6. Split temporal (respetando orden cronológico para evitar data leakage)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # 7. Instanciación y entrenamiento de LightGBM
    model = lgb.LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=6,
        random_state=42
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
    )
    
    # 8. Predicciones y Métricas de Negocio
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    y_pred = model.predict(X_val)
    
    roc_auc = roc_auc_score(y_val, y_pred_proba)
    
    print("=" * 60)
    print("RESULTADOS DE EVALUACIÓN DEL MODELO - CAPA PROCESADA (ESTADO: NO_ASISTIO)")
    print("=" * 60)
    print(f"ROC-AUC Score: {roc_auc:.4f}\n")
    print("Reporte de Clasificación:")
    print(classification_report(y_val, y_pred))
    print("=" * 60)
    
    # 9. Generación de Gráfica de Importancia de Características
    fig, ax = plt.subplots(figsize=(10, 6))
    lgb.plot_importance(model, ax=ax, importance_type='gain', color='#1E293B')
    plt.title("Importancia de Características (Feature Gain) - Capa Procesada", fontsize=12, fontweight='bold', color='#1E293B')
    plt.xlabel("Ganancia Promedio (Gain)", fontsize=10)
    plt.ylabel("Variables Predictoras", fontsize=10)
    plt.tight_layout()
    
    plt.savefig("importancia_caracteristicas_ausentismo.png", dpi=300)
    print("Gráfica guardada exitosamente como: 'importancia_caracteristicas_ausentismo.png'")
    plt.show()
    
    return model

if __name__ == "__main__":
    entrenar_y_evaluar_modelo()