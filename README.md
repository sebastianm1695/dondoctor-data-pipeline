# DonDoctor Data Pipeline & Data Governance

Este repositorio contiene la solución a la prueba técnica de arquitectura e ingeniería de datos para **DonDoctor**. Implementa un pipeline modular en Python diseñado bajo buenas prácticas de DataOps, enmascaramiento de datos personales (PII) e integración de fuentes heterogéneas.

El uso de la IA fue para verificar errores dentro del codigo y corrección en redacción.

## Bloque 1: Calidad de Datos y Gobernanza (Habeas Data)

### 1. Diagnóstico de Calidad y Hallazgos por Fuente

Tras la ejecución del script de perfilamiento (`bloque_1_profiling.py`) sobre los datos crudos, se identificaron varios retos operativos y de calidad que justifican la necesidad de la capa de transformación:

* **IPS Norte (`ips_norte_citas.csv`):**
  * Se detectaron **198 citas duplicadas** en la llave primaria `cita_id` (de 6,555 registros totales, solo 6,357 son únicos).
  * En cuanto a privacidad, el ID del paciente ya se encontraba enmascarado (`paciente_id`), lo cual cumple con las buenas prácticas de la industria.
  * Los campos con alta tasa de nulos (`motivo_cierre` con 80.7% y `observaciones` con 95.1%) corresponden a la naturaleza del negocio, ya que solo se enriqueren cuando una cita se cancela, reagenda o requiere un seguimiento especial.

* **IPS Sur (`ips_sur_citas.csv`):**
  * Presenta un **riesgo crítico de seguridad y cumplimiento legal**: las columnas `documento_identidad` y `telefono` se encuentran expuestas en texto plano.
  * No se registraron datos duplicados en sus 5,312 citas. La relación entre pacientes y datos personales es consistente (1,885 pacientes únicos para 1,885 documentos y teléfonos únicos).

* **IPS Occidente (`ips_occidente_citas.csv`):**
  * Es la fuente más heterogénea en términos de esquema. Maneja nombres de columnas distintos (`id_cita`, `genero`, `regimen_salud`, `fecha_hora_cita`, `estado_cita`).
  * Los estados de las citas se encuentran abreviados (`ATD`, `CAN`, `NAS`), por lo que requieren homologación a un dominio estándar.
  * Las fechas utilizan el formato ISO 8601 con separador `T` (ej. `2025-08-04T20:20:00`), a diferencia del espacio simple usado por las IPS Norte y Sur.

* **WhatsApp Eventos (`whatsapp_eventos.jsonl`):**
  * Es una fuente semi-estructurada de 38,416 eventos con **1,795 registros duplicados** en `_id`.
  * Se evidenció una **fuga indirecta de PII**: dentro del objeto JSON anidado en la columna `mensaje`, la clave `destinatario` incluye el número de teléfono móvil completo (ej. `+573273834925`).
  * En la columna `contexto`, la clave `ref_cita` no siempre está presente, lo que requiere un manejo condicional para evitar rupturas en el cruce relacional con las citas de las IPS.


### 2. Estrategia de Gobernanza y Cumplimiento Normativo (Ley 1581)

Para garantizar la protección de datos personales (Habeas Data) y la integridad técnica del pipeline:

1. **Anonimización Criptográfica (SHA-256 + Salt):**
   * Se aplicó un enmascaramiento unidireccional mediante el algoritmo **SHA-256 acoplado a un Salt secreto** (`SALT_SECRET`) sobre las columnas `documento_identidad`, `telefono` y el número extraído del JSON de WhatsApp. Esto permite cruzar la información entre fuentes sin exponer el dato crudo.
   * La carpeta `data/raw/` se excluyó explícitamente en el `.gitignore` para prevenir cualquier subida accidental de información sensible al repositorio remoto de Git.

2. **Reglas de Transformación para la Capa Silver:**
   * **Deduplicación:** Se eliminaron los registros duplicados exactos usando la combinación `(cita_id, ips_origen)` en Norte y el `_id` en WhatsApp.
   * **Estandarización de Esquema:** Se realizó el renombrado y casteo explícito de los campos de IPS Occidente para acoplarlos al esquema unificado.
   * **Homologación de Dominios:** Se mapearon los estados abreviados (`ATD` $\rightarrow$ `ATENDIDA`, `CAN` $\rightarrow$ `CANCELADA`, `NAS` $\rightarrow$ `NO_ASISTIO`).
   * **Aplanamiento de Objetos JSON:** Se extrajeron de forma estructurada los campos `destinatario`, `plantilla`, `ips` y `ref_cita` desde las columnas JSON de WhatsApp.

### 3. Arquitectura del Proyecto (Patrón Medallion)

El repositorio está estructurado en tres capas analíticas:
1. **Raw (Capa Cruda):** Ingesta de los archivos fuente originales en CSV y JSON sin alteraciones, preservando la traza original.
2. **Silver (Capa Limpia e Homologada):** 
   - Homologación de dominios (unificación de estados como `ATD` a `ATENDIDA`, géneros y normalización de formatos de fecha).
   - Aplicación de seudónimos criptográficos (`SHA-256` con el *Salt* institucional `SALT_SECRET = "DonDoctor_HabeasData_2026_Key"`) para proteger los datos sensibles de los pacientes (`paciente_hash`), logrando un anonimato irreversible pero permitiendo cruces deterministas entre fuentes.
3. **Gold (Capa de Consumo / Modelo Dimensional):**
   - Construcción de un esquema en estrella optimizado para analítica.
   - Creación de la tabla de hechos (`fact_citas`) y dimensiones clave (`dim_paciente`, `dim_ips`, `dim_tiempo`).
   - Cálculo oficial de la métrica de negocio: `es_ausentismo` (1 cuando el estado es `NO_ASISTIO`, 0 en caso contrario).

### 4. Estructura del Repositorio

dondoctor-pipeline/
│
├── data/
│   ├── raw/            # Archivos fuente originales
│   ├── processed/      # Tablas limpias de la Capa Silver
│   └── gold/           # Modelo dimensional (Hechos y Dimensiones)
│
├── src/
│   ├── pipelines/
│   │   ├── bloque_1_profiling.py       # Diagnóstico y calidad de datos
│   │   ├── bloque_2_transformation.py  # Limpieza, homologación y hashing PII
│   │   └── bloque_3_gold.py            # Modelado dimensional (Capa Gold)
│   └── utils/
│       └── logger.py                   # Utilidad de registro de eventos
│
├── tests/              # Pruebas unitarias (pytest)
├── requirements.txt    # Dependencias del proyecto
└── README.md           # Documentación técnica

### Resultados de Validacion del Modelo
* ROC-AUC Score: 0.9735
* Precision en Ausentismo (Clase 1): 0.92
* Recall en Ausentismo (Clase 1): 0.93
* Exactitud Global (Accuracy): 0.98

### Caracteristicas Principales Evaluadas (Feature Engineering)
1. Variables Demograficas y de Contexto: Edad, sexo, regimen, localidad y sede deatendida.
2. Variables Temporales y de la Cita: Antelacion del agendamiento calculada entre fecha_creacion y fecha_cita, dia de la semana y hora de la cita.
3. Variables Operativas: Canal de agendamiento, estado de recordatorio enviado y confirmacion previa.