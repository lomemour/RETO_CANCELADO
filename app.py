import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO EDITORIAL
# ==========================================
st.set_page_config(
    page_title="TrustGuard · Caso Cancelado",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    
    .main-title {
        font-weight: 600;
        font-size: 2.2rem;
        letter-spacing: -0.025em;
        color: #10181d;
        margin-bottom: 0px;
    }
    
    .subtitle {
        font-size: 1rem;
        color: #55656d;
        margin-bottom: 25px;
    }
    
    .card-kpi {
        background: #ffffff;
        border: 1px solid rgba(16, 24, 29, 0.1);
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    .card-kpi .val {
        font-size: 1.6rem;
        font-weight: 600;
        color: #10181d;
        letter-spacing: -0.02em;
    }
    
    .card-kpi .lbl {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #75868f;
        margin-top: 4px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f3f4;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        color: #42545e;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0b6e6e !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CARGA Y PROCESAMIENTO DE DATOS
# ==========================================
@st.cache_data
def load_and_process_data():
    df = pd.read_csv("BASE.csv")
    
    # Limpieza y preparación basada en los hallazgos de la bitácora[cite: 1, 2]
    df['Antigüedad_Cuenta_Dias'] = df['Antigüedad_Cuenta_Dias'].fillna(df['Antigüedad_Cuenta_Dias'].median())
    df['Num_Interacciones'] = df['Num_Interacciones'].fillna(0)
    df['Fecha_Hora_Publicacion'] = pd.to_datetime(df['Fecha_Hora_Publicacion'])
    
    # Ingeniería de Features: Índice de Sospecha[cite: 1, 2]
    dias_seguros = df['Antigüedad_Cuenta_Dias'].replace(0, 0.5) 
    df['Score_Sospecha'] = (df['Velocidad_Viralizacion'] / dias_seguros) * 100
    df['Score_Sospecha'] = np.clip(df['Score_Sospecha'], 0, 100)
    
    # Semáforo de Confiabilidad[cite: 1, 2]
    condiciones = [
        (df['Contenido_Reciclado'] == 'Sí') | (df['Perfil_Usuario'] == 'Bot_Sospechoso') | (df['Score_Sospecha'] > 75),
        (df['Score_Sospecha'] > 30) & (df['Score_Sospecha'] <= 75),
        (df['Score_Sospecha'] <= 30) & (df['Contenido_Reciclado'] != 'Sí')
    ]
    etiquetas = ['🔴 Rojo (Ruido Fabricado)', '🟡 Amarillo (Dudoso)', '🟢 Verde (Señal Real)']
    df['Veredicto'] = np.select(condiciones, etiquetas, default='🟡 Amarillo (Dudoso)')
    
    return df

try:
    df = load_and_process_data()
except Exception as e:
    st.error(f"Error al cargar BASE.csv. Asegúrate de que el archivo esté en el repositorio. Detalle: {e}")
    st.stop()

# ==========================================
# 3. BARRA LATERAL (FILTROS GLOBALES)
# ==========================================
st.sidebar.markdown("### 🎛️ Controles de Análisis")
st.sidebar.markdown("Filtros globales para la segmentación de evidencias en tiempo real.")

plataformas_sel = st.sidebar.multiselect("Plataforma:", df['Plataforma'].unique(), default=df['Plataforma'].unique())
perfiles_sel = st.sidebar.multiselect("Perfil de Usuario:", df['Perfil_Usuario'].unique(), default=df['Perfil_Usuario'].unique())
veredictos_sel = st.sidebar.multiselect("Veredicto:", df['Veredicto'].unique(), default=df['Veredicto'].unique())

df_filtered = df[
    (df['Plataforma'].isin(plataformas_sel)) & 
    (df['Perfil_Usuario'].isin(perfiles_sel)) & 
    (df['Veredicto'].isin(veredictos_sel))
]

# ==========================================
# 4. ENCABEZADO Y KPIS ESTILIZADOS
# ==========================================
st.markdown('<p class="main-title">🛡️ TRUSTGUARD · Panel de Inteligencia</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Auditoría algorítmica y separación de señal vs. ruido para el caso de crisis digital de Kai Duarte[cite: 1].</p>', unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
total_reg = len(df_filtered)
rojos_reg = len(df_filtered[df_filtered['Veredicto'] == '🔴 Rojo (Ruido Fabricado)'])
vel_max = df_filtered['Velocidad_Viralizacion'].max()
reciclados = len(df_filtered[df_filtered['Contenido_Reciclado'] == 'Sí'])

with k1:
    st.markdown(f'<div class="card-kpi"><div class="val">{total_reg:,}</div><div class="lbl">Registros Analizados</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="card-kpi"><div class="val" style="color: #c2402d;">{rojos_reg:,}</div><div class="lbl">Alertas Rojas</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="card-kpi"><div class="val">{vel_max:,.1f}</div><div class="lbl">Velocidad Máx (ints/min)</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="card-kpi"><div class="val">{reciclados:,}</div><div class="lbl">Contenido Reciclado</div></div>', unsafe_allow_html=True)

st.write("")
st.write("")

# ==========================================
# 5. PESTAÑAS PRINCIPALES
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Propagación Temporal", 
    "🔍 Auditoría Explicable (XAI)", 
    "🗺️ Mapa de Coordinación", 
    "📋 Módulo Completo de Tablas Analíticas"
])

# --- TAB 1: PROPAGACIÓN ---
with tab1:
    st.markdown("### Evolución del Escándalo en el Tiempo")
    st.markdown("Distribución cronológica de publicaciones segmentada por veredicto algorítmico[cite: 1, 2].")
    
    fig_timeline = px.histogram(
        df_filtered, x="Fecha_Hora_Publicacion", color="Veredicto",
        color_discrete_map={
            '🔴 Rojo (Ruido Fabricado)':'#c2402d', 
            '🟡 Amarillo (Dudoso)':'#b07100', 
            '🟢 Verde (Señal Real)':'#14713f'
        },
        nbins=60, hover_data=["Plataforma"]
    )
    fig_timeline.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Fecha y Hora de Publicación",
        yaxis_title="Volumen",
        hovermode="x unified"
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

# --- TAB 2: AUDITORÍA XAI ---
with tab2:
    st.markdown("### Auditoría de Evidencias (Explicabilidad Local)")
    st.markdown("Selecciona una cuenta marcada como **Rojo** para auditar los factores matemáticos que motivaron la alerta[cite: 2].")
    
    df_rojos = df[df['Veredicto'] == '🔴 Rojo (Ruido Fabricado)']
    if len(df_rojos) > 0:
        opciones = df_rojos['Usuario_Handle'].astype(str) + " (ID: " + df_rojos['ID_Publicacion'].astype(str) + ")"
        seleccion = st.selectbox("Seleccionar cuenta sospechosa:", opciones)
        
        if seleccion:
            id_sel = int(seleccion.split("(ID: ")[1].replace(")", ""))
            pub = df[df['ID_Publicacion'] == id_sel].iloc[0]
            
            st.info(f"**Texto Registrado:** *'{pub['Texto_Publicacion']}'*")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Antigüedad de Cuenta", f"{pub['Antigüedad_Cuenta_Dias']} días")
            m2.metric("Velocidad de Viralización", f"{pub['Velocidad_Viralizacion']} ints/min")
            m3.metric("Contenido Reciclado", pub['Contenido_Reciclado'])
            
            st.markdown(f"**Índice de Sospecha Calculado:** `{int(pub['Score_Sospecha'])} / 100`")
            st.progress(int(pub['Score_Sospecha']))
    else:
        st.warning("No hay registros en rojo bajo los filtros actuales.")

# --- TAB 3: MAPA DE COORDINACIÓN ---
with tab3:
    st.markdown("### Mapa de Coordinación y Anomalías")
    st.markdown("El tamaño de la burbuja representa el volumen de interacciones. Las burbujas masivas a la izquierda delatan cuentas nuevas con impacto coordinado[cite: 1, 2].")
    
    df_burbujas = df_filtered.copy()
    df_burbujas['Interacciones_Visual'] = df_burbujas['Num_Interacciones'].clip(lower=10)
    
    fig_scatter = px.scatter(
        df_burbujas, x="Antigüedad_Cuenta_Dias", y="Velocidad_Viralizacion", 
        color="Veredicto", size="Interacciones_Visual",
        hover_data=["Usuario_Handle", "ID_Publicacion", "Num_Interacciones", "Plataforma"],
        color_discrete_map={
            '🔴 Rojo (Ruido Fabricado)':'#c2402d', 
            '🟡 Amarillo (Dudoso)':'#b07100', 
            '🟢 Verde (Señal Real)':'#14713f'
        },
        opacity=0.75, size_max=40
    )
    fig_scatter.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    fig_scatter.add_hline(y=10, line_dash="dash", line_color="#c2402d", annotation_text="Umbral de Velocidad Anómala")
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- TAB 4: MÓDULO COMPLETO DE TABLAS ANALÍTICAS ---
with tab4:
    st.markdown("### 📊 Tablas Analíticas Especializadas del Caso")
    st.markdown("Exploración detallada de las estructuras cuantitativas desarrolladas durante la investigación.")
    
    subtab1, subtab2, subtab3, subtab4, subtab5 = st.tabs([
        "🚨 1. Top Cuentas Sospechosas", 
        "🔬 2. Firma Comportamental", 
        "⚖️ 3. Afirmaciones Sustantivas", 
        "💼 4. Matriz de Decisiones y Costos", 
        "📋 5. Explorador de Datos Crudos"
    ])
    
    with subtab1:
        st.markdown("#### Tabla 3 del Proyecto: Cuentas con Mayor Anomalía")
        st.markdown("Ranking de las cuentas detectadas con mayor puntaje de sospecha estructural y validación de bots[cite: 2].")
        
        df_cuentas_top = df.sort_values(by="Score_Sospecha", ascending=False).head(10)[
            ['Usuario_Handle', 'Score_Sospecha', 'Antigüedad_Cuenta_Dias', 'Num_Seguidores_Cuenta', 'Plataforma', 'Perfil_Usuario']
        ].drop_duplicates(subset=['Usuario_Handle'])
        
        st.dataframe(
            df_cuentas_top,
            use_container_width=True,
            column_config={
                "Score_Sospecha": st.column_config.ProgressColumn(
                    "Puntaje Sospecha",
                    help="Nivel de anomalía detectado (0-100)",
                    format="%.1f",
                    min_value=0,
                    max_value=100
                ),
                "Num_Seguidores_Cuenta": st.column_config.NumberColumn(
                    "Seguidores",
                    format="%d"
                ),
                "Antigüedad_Cuenta_Dias": st.column_config.NumberColumn(
                    "Antigüedad (Días)",
                    format="%.1f"
                )
            }
        )
        
    with subtab2:
        st.markdown("#### Tabla Comparativa: Firma Comportamental")
        st.markdown("Diferencias cuantitativas fundamentales entre las cuentas de brigada/bots y el resto de usuarios orgánicos[cite: 1].")
        
        data_firma = {
            "Métrica Evaluada": [
                "Seguidores ganados por día de vida (promedio)",
                "Velocidad de viralización (mediana en ints/min)",
                "Diversidad léxica (textos únicos / totales)",
                "Densidad de uso de mayúsculas"
            ],
            "Bot / Sospechoso": [
                "4.764[cite: 1]", 
                "14.95[cite: 1]", 
                "0.63[cite: 1]", 
                "15.7 %[cite: 1]"
            ],
            "Resto de Usuarios (Orgánicos)": [
                "4 – 27[cite: 1]", 
                "2.3 – 3.0[cite: 1]", 
                "1.00[cite: 1]", 
                "0.8 %[cite: 1]"
            ]
        }
        df_firma = pd.DataFrame(data_firma)
        st.dataframe(df_firma, use_container_width=True, hide_index=True)
        
    with subtab3:
        st.markdown("#### Balance de Afirmaciones Sustantivas del Caso")
        st.markdown("Distribución del peso probatorio entre los argumentos que incriminan frente a los que exculpan[cite: 1, 2].")
        
        data_afirmaciones = {
            "Dimensión Analizada": [
                "Afirmaciones distintas identificadas",
                "Publicaciones que las sostienen",
                "Confiabilidad media (0–100)",
                "Corroboraciones independientes (promedio)",
                "Antigüedad mediana de la cuenta",
                "Peso probatorio total acumulado"
            ],
            "Bando que Incrimina": [
                "4[cite: 1, 2]",
                "89[cite: 1, 2]",
                "36,8[cite: 1, 2]",
                "0,42[cite: 1, 2]",
                "2,6 días[cite: 1, 2]",
                "1,69 (8,1 % del total)[cite: 1, 2]"
            ],
            "Bando que Exculpa": [
                "10[cite: 1, 2]",
                "225[cite: 1, 2]",
                "69,9[cite: 1, 2]",
                "2,11[cite: 1, 2]",
                "632,8 días[cite: 1, 2]",
                "19,19 (91,9 % del total)[cite: 1, 2]"
            ]
        }
        df_afirmaciones = pd.DataFrame(data_afirmaciones)
        st.dataframe(df_afirmaciones, use_container_width=True, hide_index=True)

    with subtab4:
        st.markdown("#### Tabla 4 del Proyecto: Supuestos de Costo y Arrepentimiento")
        st.markdown("Pérdida esperada en múltiplos del valor anual del contrato para fundamentar la recomendación de negocio[cite: 2].")
        
        data_costos = {
            "Acción a las 6:00 a.m.": [
                "Mantener el patrocinio",
                "Pausar 72 horas",
                "Romper el contrato"
            ],
            "Si la acusación era cierta (Pérdida)": [
                "2,5 × contrato[cite: 2]",
                "0,8 × contrato[cite: 2]",
                "0,3 × contrato[cite: 2]"
            ],
            "Si la acusación era falsa (Pérdida)": [
                "0,0 × contrato[cite: 2]",
                "0,1 × contrato[cite: 2]",
                "1,8 × contrato[cite: 2]"
            ],
            "Arrepentimiento Máximo (Peor caso)": [
                "0,1839[cite: 2]",
                "0,0002 (Óptimo)[cite: 2]",
                "1,4762[cite: 2]"
            ]
        }
        df_costos = pd.DataFrame(data_costos)
        st.dataframe(df_costos, use_container_width=True, hide_index=True)

    with subtab5:
        st.markdown("#### Explorador General de Registros Procesados")
        st.markdown("Base de datos completa con los veredictos y métricas aplicadas a cada publicación[cite: 1, 2].")
        
        st.dataframe(
            df_filtered[['ID_Publicacion', 'Usuario_Handle', 'Plataforma', 'Perfil_Usuario', 'Veredicto', 'Score_Sospecha', 'Velocidad_Viralizacion', 'Contenido_Reciclado']],
            use_container_width=True,
            height=400,
            column_config={
                "Score_Sospecha": st.column_config.ProgressColumn(
                    "Índice Sospecha",
                    help="Puntaje de anomalía de 0 a 100",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                ),
                "Velocidad_Viralizacion": st.column_config.NumberColumn(
                    "Velocidad (ints/min)",
                    format="%.1f"
                )
            }
        )
