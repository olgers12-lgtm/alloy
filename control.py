# app_alloy_streamlit.py
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Alloy Dashboard", page_icon="⚙️", layout="wide")

st.title("⚙️ Alloy Dashboard Industrial")
st.markdown("Visualiza y controla tu consumo de Alloy con recuperación y pérdidas mínimas.")

# --- Conexión a Google Sheets ---
COLUMNS = [
    "Peso Alloy (lbs)", "Máquinas", "Trabajos Estándar", "Trabajos Free",
    "Alloy Necesario (lbs)", "Pérdida Total (lbs)", "Alloy a Pedir (lbs)"
]

@st.cache_data(show_spinner=False, ttl=0)
def load_registros_from_gsheets() -> pd.DataFrame:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # La URL del spreadsheet la defines en Secrets; ver instrucciones abajo.
        df = conn.read(worksheet="Registros", ttl=0)
        df = pd.DataFrame(df)
        # Limpia filas totalmente vacías y asegura columnas
        if df.empty:
            return pd.DataFrame(columns=COLUMNS)
        # Asegura el orden de columnas
        missing = [c for c in COLUMNS if c not in df.columns]
        for c in missing:
            df[c] = pd.NA
        return df[COLUMNS]
    except Exception as e:
        st.warning(f"No se pudo cargar registros desde Google Sheets: {e}")
        return pd.DataFrame(columns=COLUMNS)

def save_registro_to_gsheets(nuevo_registro: dict):
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Vuelve a leer para evitar sobrescribir cambios de otros
    df_actual = conn.read(worksheet="Registros", ttl=0)
    df_actual = pd.DataFrame(df_actual)
    if df_actual.empty:
        df_actual = pd.DataFrame(columns=COLUMNS)
    # Asegura columnas
    missing = [c for c in COLUMNS if c not in df_actual.columns]
    for c in missing:
        df_actual[c] = pd.NA
    df_actual = df_actual[COLUMNS]

    df_nuevo = pd.concat([df_actual, pd.DataFrame([nuevo_registro])], ignore_index=True)
    conn.update(worksheet="Registros", data=df_nuevo)

# --- Sidebar ---
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

# Pérdida mínima por trabajo (0.1 g)
perdida_por_trabajo_lbs = 0.000220462
perdida_total = (trabajos_estandar + trabajos_free) * perdida_por_trabajo_lbs

# Alloy necesario total
alloy_total_necesario = requerimiento_fijo + perdida_total

# Evaluación
sobrante = peso_lbs - alloy_total_necesario
necesita_pedir = sobrante < 0
alloy_a_pedir = abs(sobrante) if necesita_pedir else 0

# --- Métricas visuales ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Alloy Disponible (lbs)", f"{peso_lbs:,.2f}")
col2.metric("Requerimiento Fijo (lbs)", f"{requerimiento_fijo:,.2f}")
col3.metric("Pérdida Total (lbs)", f"{perdida_total:,.4f}")
col4.metric("Alloy a Pedir (lbs)", f"{alloy_a_pedir:,.2f}")

# --- Gráfica barras con Plotly ---
st.subheader("📊 Comparación Alloy Disponible vs Necesario")
bar_fig = go.Figure(data=[
    go.Bar(name='Disponible', x=['Alloy'], y=[peso_lbs], marker_color='green'),
    go.Bar(name='Requerido + Pérdida', x=['Alloy'], y=[alloy_total_necesario], marker_color='orange')
])
bar_fig.update_layout(barmode='group', yaxis_title='Libras', template='plotly_white')
st.plotly_chart(bar_fig, use_container_width=True)

# --- Gauge (Velocímetro) ---
st.subheader("⏱️ Nivel de Alloy Disponible")
max_val = max(peso_lbs, alloy_total_necesario) * 1.2  # escala
gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=peso_lbs,
    title={'text': "Alloy Disponible (lbs)"},
    gauge={'axis': {'range': [0, max_val]},
           'bar': {'color': "green"},
           'steps': [
               {'range': [0, alloy_total_necesario], 'color': "orange"},
               {'range': [alloy_total_necesario, max_val], 'color': "lightgreen"}]}))
st.plotly_chart(gauge, use_container_width=True)

# --- Registro histórico (persistente) ---
st.subheader("📑 Registros de control")
if "registros" not in st.session_state:
    st.session_state["registros"] = load_registros_from_gsheets()

# Botón para guardar (anexa y sube a Sheets)
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
    # Guarda en Google Sheets
    save_registro_to_gsheets(nuevo_registro)
    # Refresca tabla local
    st.session_state["registros"] = load_registros_from_gsheets()
    st.success("Registro guardado en Google Sheets.")

st.dataframe(st.session_state["registros"], use_container_width=True)

# Descargar Excel
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    st.session_state["registros"].to_excel(writer, index=False, sheet_name="Registros")
buffer.seek(0)

st.download_button(
    label="📥 Descargar registros en Excel",
    data=buffer.getvalue(),
    file_name="Registros_Alloy.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
