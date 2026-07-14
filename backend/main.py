from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import numpy as np
import pandas as pd
import sklearn as sklearn
from pydantic import BaseModel

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Cargar el modelo y el escalador utilizando rutas absolutas relativas al archivo
modelo_xgb = joblib.load(os.path.join(BASE_DIR, 'best_model_XGB.joblib'))
scaler = joblib.load(os.path.join(BASE_DIR, 'scaler.joblib')) 

app = FastAPI(
    title="API Riesgo Cardiovascular - Proyecto de Tesis",
    description="Motor de inferencia con Feature Engineering avanzado"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen (luego lo restringiremos a tu dominio de Vercel)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "API de Riesgo Cardiovascular activa"}

# 2. El usuario solo envía 11 variables puras (las del formulario clínico)
class DatosPaciente(BaseModel):
    age: int          # Edad en DÍAS (como lo espera tu script original)
    gender: int       # 1 para mujeres, 2 para hombres (si está en tu dataset)
    height: float     # Altura en cm
    weight: float     # Peso en kg
    ap_hi: float      # Presión Sistólica
    ap_lo: float      # Presión Diastólica
    cholesterol: int  # 1: Normal, 2: Alto, 3: Muy alto
    gluc: int         # 1: Normal, 2: Alta, 3: Muy alta
    smoke: int        # Fuma: 1 sí, 0 no
    alco: int         # Toma alcohol: 1 sí, 0 no
    active: int       # Hace ejercicio: 1 sí, 0 no

@app.post("/predecir")
def hacer_prediccion(paciente: DatosPaciente):
    # Convertimos a DataFrame
    df = pd.DataFrame([paciente.model_dump()])

    # Convertimos la edad de días a años
    df['edad_años'] = df['age'] / 365.25
    
    # 3. Calculamos IMC (ya que tu script asume que ya existe)
    df['imc'] = df['weight'] / ((df['height'] / 100) ** 2)

    # ---------------------------------------------------------
    # 4. REPLICAMOS TU FEATURE ENGINEERING EXACTO
    # ---------------------------------------------------------
    df['pulse_pressure'] = df['ap_hi'] - df['ap_lo']
    df['map'] = (df['ap_hi'] + 2 * df['ap_lo']) / 3
    df['pressure_ratio'] = df['pulse_pressure'] / df['ap_hi']
    
    df['imc_categoria'] = pd.cut(
        df['imc'], bins=[0, 18.5, 25, 30, 35, 100], labels=[0, 1, 2, 3, 4], include_lowest=True
    ).astype(int)
    
    df['edad_grupo'] = pd.cut(
        df['age'] / 365.25, bins=[0, 40, 50, 60, 100], labels=[0, 1, 2, 3], include_lowest=True
    ).astype(int)
    
    def categorize_hypertension(row):
        if row['ap_hi'] >= 180 or row['ap_lo'] >= 120: return 4
        elif row['ap_hi'] >= 140 or row['ap_lo'] >= 90: return 3
        elif row['ap_hi'] >= 130 or row['ap_lo'] >= 80: return 2
        else: return 1
        
    df['hipertension_nivel'] = df.apply(categorize_hypertension, axis=1)
    
    df['imc_edad_interaction'] = (df['imc'] * df['age'] / 365.25) / 100
    df['presion_imc_interaction'] = (df['map'] * df['imc']) / 100
    df['colesterol_glucosa_interaction'] = df['cholesterol'] * df['gluc']
    df['lifestyle_score'] = df['smoke'] * 2 + df['alco'] * 1 - df['active'] * 1.5
    
    df['risk_factor_count'] = (
        (df['cholesterol'] > 1).astype(int) +
        (df['gluc'] > 1).astype(int) +
        df['smoke'] +
        (df['imc'] >= 25).astype(int) +
        (df['active'] == 0).astype(int)
    )
    
    df['edad_squared'] = (df['age'] / 365.25) ** 2
    df['imc_squared'] = df['imc'] ** 2
    df['log_ap_hi'] = np.log1p(df['ap_hi'])
    df['col_gluc_ratio'] = df['cholesterol'] / (df['gluc'] + 0.5)

    # ---------------------------------------------------------
    # 5. ALINEACIÓN INTELIGENTE DE COLUMNAS
    # ---------------------------------------------------------
    # En lugar de adivinar qué 24 columnas sobrevivieron al 'VarianceThreshold',
    # le pedimos al propio modelo XGBoost cuáles son las que necesita y en qué orden.
    columnas_requeridas = modelo_xgb.feature_names_in_
    df_final = df[columnas_requeridas]

    # ---------------------------------------------------------
    # 6. ESCALADO Y PREDICCIÓN
    # ---------------------------------------------------------
    # 1. Transformamos los datos con el escalador
    datos_escalados = scaler.transform(df_final)
    
    # 2. Volvemos a armar el DataFrame con los nombres de las columnas para XGBoost
    df_escalado_final = pd.DataFrame(datos_escalados, columns=df_final.columns)

    # 3. Hacemos la predicción DEFINITIVA usando los datos escalados
    prediccion = modelo_xgb.predict(df_escalado_final)
    probabilidad = modelo_xgb.predict_proba(df_escalado_final)[0][1]
    
    return {
        "riesgo_cardiovascular": int(prediccion[0]),
        "probabilidad_porcentaje": round(float(probabilidad) * 100, 2),
        "mensaje": "Alto riesgo" if prediccion[0] == 1 else "Bajo riesgo"
    }