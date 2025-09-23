import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Control de Alloy", page_icon="⚙️", layout="centered")

st.title("⚙️ Control de Alloy")
st.write("Calculadora y registro de requerimiento y disponibilidad de Alloy")

# --- Inputs ---
st.header("📥 Ingreso de datos")

peso_kg = st.number_input("Peso actual de Alloy (kg)", min_value=0.0, value=0.0, step=1.0)
num_maquinas = st.number_input("Número de máquinas", min_value=1, value=2, step=1)
alloy_por_maquina = st.number_input("Alloy por máquina (lbs)", min_value=0.0, value=35.0, step=1.0)
superficies = st.number_input("Superficies (lbs)", min_value=0.0, value=50.0, step=1.0)
recuperadora = st.number_input("Recuperadora (lbs)", min_value=0.0, value=17.0, step=1.0)

trabajos_estandar = st.number_input("Trabajos Estándar en proceso", min_value=0, value=0, step=1)
trabajos_free = st.number_input("Trabajos Free en proceso", min_value=0, value=0, step=1)

# --- Cálculos ---
lbs_disponible = peso_kg * 2.20462
requerimiento_maquinas = num_maquinas * alloy_por_maquina
consumo_trabajos = trabajos_estandar * 0.78 + trabajos_free * 0.30
total_requerido = requerimiento_maquinas + superficies + recuperadora + consumo_trabajos
sobrante = lbs_disponible - total_requerido

# --- Resultados ---
st.header("📊 Resultados")
st.write(f"**Alloy disponible (lbs):** {lbs_disponible:.2f}")
st.write(f"**Requerimiento máquinas (lbs):** {requerimiento_maquinas:.2f}")
st.write(f"**Consumo trabajos (lbs):** {consumo_trabajos:.2f}")
st.write(f"**Total requerido (lbs):** {total_requerido:.2f}")
st.write(f"**Alloy sobrante (lbs):** {sobrante:.2f}")

estado = "SUFICIENTE"
if sobrante < 0:
    estado = "PEDIR MÁS ALLOY"
    st.error(f"⚠️ PEDIR MÁS ALLOY. Faltan {-sobrante:.2f} lbs.")
else:
    st.success("✅ Suficiente Alloy disponible.")

# --- Registro ---
st.header("📝 Guardar registro")

if st.button("Guardar registro"):
    # Cargar historial existente
    file_name = "historial_alloy.csv"
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
    else:
        df = pd.DataFrame(columns=["FechaHora","Peso_kg","Num_maquinas","Alloy_maquina_lbs","Superficies_lbs",
                                   "Recuperadora_lbs","Trabajos_estandar","Trabajos_free","Disponible_lbs",
                                   "Requerimiento_maquinas","Consumo_trabajos","Total_requerido","Sobrante","Estado"])
    
    new_row = {
        "FechaHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Peso_kg": peso_kg,
        "Num_maquinas": num_maquinas,
        "Alloy_maquina_lbs": alloy_por_maquina,
        "Superficies_lbs": superficies,
        "Recuperadora_lbs": recuperadora,
        "Trabajos_estandar": trabajos_estandar,
        "Trabajos_free": trabajos_free,
        "Disponible_lbs": lbs_disponible,
        "Requerimiento_maquinas": requerimiento_maquinas,
        "Consumo_trabajos": consumo_trabajos,
        "Total_requerido": total_requerido,
        "Sobrante": sobrante,
        "Estado": estado
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(file_name, index=False)
    st.success("Registro guardado correctamente ✅")

# --- Ver historial ---
st.header("📂 Historial de registros")
file_name = "historial_alloy.csv"
if os.path.exists(file_name):
    df = pd.read_csv(file_name)
    st.dataframe(df)
else:
    st.info("No hay registros todavía.")

