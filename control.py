# app_alloy.py
import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="Alloy Dashboard", layout="wide")

st.title("⚙️ Alloy Dashboard Industrial")
st.markdown("Visualiza y controla tu consumo de Alloy con recuperación y pérdidas mínimas.")

# --- Inputs ---
st.sidebar.header("🔧 Parámetros de proceso")
peso_kg = st.sidebar.number_input("Peso actual de Alloy (kg)", value=50.0, step=1.0)
num_maquinas = st.sidebar.number_input("Número de máquinas", value=2, step=1)
alloy_por_maquina = st.sidebar.number_input("Alloy por máquina (lbs)", value=35.0, step=1.0)
alloy_superficie = st.sidebar.number_input("Alloy línea superficies (lbs)", value=50.0, step=1.0)
alloy_recuperadora = st.sidebar.number_input("Alloy recuperadora (lbs)", value=17.0, step=1.0)

st.sidebar.subheader("🔧 Producción")
trabajos_estandar = st.sidebar.number_input("Trabajos estándar", value=100, step=1)
trabajos_free = st.sidebar.number_input("Trabajos free", value=50, step=1)

# --- Cálculos ---
peso_lbs = peso_kg * 2.20462

# Alloy fijo
requerimiento_fijo = num_maquinas * alloy_por_maquina + alloy_superficie + alloy_recuperadora

# Consumo real por trabajos (con recuperación y pérdida)
consumo_estandar = trabajos_estandar * 0.78   # lbs "en proceso"
consumo_free = trabajos_free * 0.30

# Recuperación: 99.99% se recupera, pérdida de 0.1 g/trabajo (~0.000220462 lbs/trabajo)
perdida_por_trabajo_lbs = 0.000220462
perdida_total = (trabajos_estandar + trabajos_free) * perdida_por_trabajo_lbs

# Alloy necesario total
alloy_total_necesario = requerimiento_fijo + perdida_total

# Evaluación
sobrante = peso_lbs - alloy_total_necesario
necesita_pedir = sobrante < 0
alloy_a_pedir = abs(sobrante) if necesita_pedir else 0

# --- Mostrar métricas ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Alloy Disponible (lbs)", f"{peso_lbs:,.2f}")
col2.metric("Alloy Fijo Requerido (lbs)", f"{requerimiento_fijo:,.2f}")
col3.metric("Pérdida Total (lbs)", f"{perdida_total:,.4f}")
col4.metric("Alloy a Pedir (lbs)", f"{alloy_a_pedir:,.2f}")

# --- Gráficos ---
st.subheader("📊 Visualización del consumo de Alloy")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6,4))
labels = ['Disponible', 'Requerido + Pérdida']
values = [peso_lbs, alloy_total_necesario]
ax.bar(labels, values, color=['#4CAF50','#FF5722'])
ax.set_ylabel('Libras')
ax.set_title('Comparación Alloy Disponible vs Necesario')
st.pyplot(fig)

# --- Registro histórico ---
st.subheader("📑 Registros de control")
if "registros" not in st.session_state:
    st.session_state["registros"] = pd.DataFrame(columns=[
        "Peso Alloy (lbs)", "Máquinas", "Trabajos Estándar", "Trabajos Free",
        "Alloy Necesario (lbs)", "Pérdida Total (lbs)", "Alloy a Pedir (lbs)"
    ])

if st.button("Guardar registro"):
    nuevo_registro = {
        "Peso Alloy (lbs)": peso_lbs,
        "Máquinas": num_maquinas,
        "Trabajos Estándar": trabajos_estandar,
        "Trabajos Free": trabajos_free,
        "Alloy Necesario (lbs)": alloy_total_necesario,
        "Pérdida Total (lbs)": perdida_total,
        "Alloy a Pedir (lbs)": alloy_a_pedir
    }
    st.session_state["registros"] = pd.concat(
        [st.session_state["registros"], pd.DataFrame([nuevo_registro])],
        ignore_index=True
    )

st.dataframe(st.session_state["registros"])

# Descargar Excel
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    st.session_state["registros"].to_excel(writer, index=False, sheet_name="Registros")

st.download_button(
    label="📥 Descargar registros en Excel",
    data=buffer,
    file_name="Registros_Alloy.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
