import streamlit as st

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. CONFIGURACIÓN
st.set_page_config(page_title="TrustGuard - Caso Cancelado", layout="wide", initial_sidebar_state="expanded")

# 2. PROCESAMIENTO DE DATOS
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df['Antigüedad_Cuenta_Dias'] = df['Antigüedad_Cuenta_Dias'].fillna(df['Antigüedad_Cuenta_Dias'].median())
    df['Num_Interacciones'] = df['Num_Interacciones'].fillna(0)
    df['Fecha_Hora_Publicacion'] = pd.to_datetime(df['Fecha_Hora_Publicacion'])
    
    # Feature Engineering
    dias_seguros = df['Antigüedad_Cuenta_Dias'].replace(0, 0.5) 
    df['Score_Sospecha'] = (df['Velocidad_Viralizacion'] / dias_seguros) * 100
    df['Score_Sospecha'] = np.clip(df['Score_Sospecha'], 0, 100)
    
    # Semáforo
    condiciones = [
        (df['Contenido_Reciclado'] == 'Sí') | (df['Perfil_Usuario'] == 'Bot_Sospechoso') | (df['Score_Sospecha'] > 75),
        (df['Score_Sospecha'] > 30) & (df['Score_Sospecha'] <= 75),
        (df['Score_Sospecha'] <= 30) & (df['Contenido_Reciclado'] != 'Sí')
    ]
    etiquetas = ['🔴 Rojo (Ruido Fabricado)', '🟡 Amarillo (Dudoso)', '🟢 Verde (Señal Real)']
    df['Veredicto'] = np.select(condiciones, etiquetas, default='🟡 Amarillo (Dudoso)')
    return df

# 3. INTERFAZ PRINCIPAL
st.title("🛡️ TrustGuard: Sistema Interactivo de Detección")
st.markdown("Analiza la propagación del rumor de Kai Duarte y separa la señal real del ruido coordinado.")

uploaded_file = st.file_uploader("📂 Sube el archivo BASE.csv para comenzar", type="csv")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    # --- BARRA LATERAL (FILTROS INTERACTIVOS) ---
    st.sidebar.header("🎛️ Filtros Globales")
    st.sidebar.markdown("Usa estos filtros para interactuar con los datos en tiempo real.")
    
    plataformas_sel = st.sidebar.multiselect("Plataforma:", df['Plataforma'].unique(), default=df['Plataforma'].unique())
    perfiles_sel = st.sidebar.multiselect("Perfil de Usuario:", df['Perfil_Usuario'].unique(), default=df['Perfil_Usuario'].unique())
    veredictos_sel = st.sidebar.multiselect("Veredicto:", df['Veredicto'].unique(), default=df['Veredicto'].unique())
    
    # Aplicar filtros
    df_filtered = df[(df['Plataforma'].isin(plataformas_sel)) & 
                     (df['Perfil_Usuario'].isin(perfiles_sel)) & 
                     (df['Veredicto'].isin(veredictos_sel))]

    # --- KPIs PRINCIPALES ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Publicaciones", f"{len(df_filtered):,}")
    col2.metric("Alertas Rojas", f"{len(df_filtered[df_filtered['Veredicto'] == '🔴 Rojo (Ruido Fabricado)']):,}")
    col3.metric("Velocidad Máx.", f"{df_filtered['Velocidad_Viralizacion'].max()} ints/min")
    col4.metric("Contenido Reciclado", f"{len(df_filtered[df_filtered['Contenido_Reciclado'] == 'Sí']):,}")
    
    st.divider()

    # --- PESTAÑAS ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Propagación", "🔍 Auditoría (XAI)", "🗺️ Mapa de Burbujas", "📋 Explorador de Datos"])
    
    with tab1:
        st.subheader("Evolución del Escándalo")
        fig_timeline = px.histogram(df_filtered, x="Fecha_Hora_Publicacion", color="Veredicto", 
                                    color_discrete_map={'🔴 Rojo (Ruido Fabricado)':'#ff4b4b', 
                                                        '🟡 Amarillo (Dudoso)':'#ffaa00', 
                                                        '🟢 Verde (Señal Real)':'#21c354'},
                                    nbins=60, hover_data=["Plataforma"])
        # Hacer el gráfico más interactivo (zoom, pan)
        fig_timeline.update_layout(xaxis_title="Hora", yaxis_title="Volumen de Publicaciones", hovermode="x unified")
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df_filtered, names='Plataforma', hole=0.4, title="Impacto por Plataforma")
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            fig_bar = px.histogram(df_filtered, y="Perfil_Usuario", color="Veredicto", barmode="stack",
                                   color_discrete_map={'🔴 Rojo (Ruido Fabricado)':'#ff4b4b', '🟡 Amarillo (Dudoso)':'#ffaa00', '🟢 Verde (Señal Real)':'#21c354'},
                                   title="Veredicto vs Tipo de Perfil")
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("Auditor de IA Explicable (XAI)")
        st.markdown("Selecciona una cuenta marcada como 'Rojo' para ver la justificación del algoritmo.")
        
        # Selector inteligente
        df_rojos = df[df['Veredicto'] == '🔴 Rojo (Ruido Fabricado)']
        opciones_usuarios = df_rojos['Usuario_Handle'].astype(str) + " (ID: " + df_rojos['ID_Publicacion'].astype(str) + ")"
        seleccion = st.selectbox("Seleccionar cuenta sospechosa para investigar:", opciones_usuarios)
        
        if seleccion:
            # Extraer el ID de la cadena seleccionada
            id_seleccionado = int(seleccion.split("(ID: ")[1].replace(")", ""))
            pub_data = df[df['ID_Publicacion'] == id_seleccionado].iloc[0]
            
            st.info(f"**Texto Analizado:** *'{pub_data['Texto_Publicacion']}'*")
            
            c_a, c_b, c_c = st.columns(3)
            c_a.metric("Usuario", pub_data['Usuario_Handle'], pub_data['Perfil_Usuario'])
            c_b.metric("Plataforma", pub_data['Plataforma'])
            c_c.metric("Veredicto", pub_data['Veredicto'])
            
            st.write("### ¿Por qué se tomó esta decisión?")
            st.progress(int(pub_data['Score_Sospecha']), text=f"Índice de Sospecha: {int(pub_data['Score_Sospecha'])}/100")
            
            c1, c2, c3 = st.columns(3)
            # Días
            estado_dias = "Anormal" if pub_data['Antigüedad_Cuenta_Dias'] < 15 else "Normal"
            color_dias = "inverse" if estado_dias == "Anormal" else "normal"
            c1.metric("Antigüedad", f"{pub_data['Antigüedad_Cuenta_Dias']} días", estado_dias, delta_color=color_dias)
            
            # Velocidad
            estado_vel = "Excesiva" if pub_data['Velocidad_Viralizacion'] > 5 else "Normal"
            color_vel = "inverse" if estado_vel == "Excesiva" else "normal"
            c2.metric("Viralización", f"{pub_data['Velocidad_Viralizacion']} inter/min", estado_vel, delta_color=color_vel)
            
            # Reciclado
            estado_rec = "Alerta!" if pub_data['Contenido_Reciclado'] == 'Sí' else "Original"
            color_rec = "inverse" if estado_rec == "Alerta!" else "normal"
            c3.metric("Reciclado", pub_data['Contenido_Reciclado'], estado_rec, delta_color=color_rec)

    with tab3:
        st.subheader("Mapa de Burbujas (Detección de Coordinación)")
        st.markdown("El **tamaño de la burbuja** representa el número total de interacciones. Busca burbujas grandes pegadas a la izquierda (Cuentas nuevas con impacto masivo).")
        # Gráfico interactivo con tamaño variable
        df_burbujas = df_filtered.copy()
        df_burbujas['Interacciones_Visual'] = df_burbujas['Num_Interacciones'].clip(lower=10) # Evitar burbujas invisibles
        
        fig_scatter = px.scatter(df_burbujas, x="Antigüedad_Cuenta_Dias", y="Velocidad_Viralizacion", 
                                 color="Veredicto", size="Interacciones_Visual",
                                 hover_data=["Usuario_Handle", "ID_Publicacion", "Num_Interacciones", "Plataforma"],
                                 color_discrete_map={'🔴 Rojo (Ruido Fabricado)':'#ff4b4b', 
                                                     '🟡 Amarillo (Dudoso)':'#ffaa00', 
                                                     '🟢 Verde (Señal Real)':'#21c354'},
                                 opacity=0.7, size_max=40)
        
        # Agregar línea de límite seguro
        fig_scatter.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="Límite Velocidad Sospechosa")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab4:
        st.subheader("Explorador de Datos Crudos")
        st.markdown("Usa esta tabla para buscar términos específicos o descargar los datos filtrados.")
        # Mostrar DataFrame de forma interactiva
        st.dataframe(df_filtered[['ID_Publicacion', 'Usuario_Handle', 'Plataforma', 'Texto_Publicacion', 'Veredicto', 'Velocidad_Viralizacion']], 
                     use_container_width=True, height=400)

else:
    st.info(" Por favor, carga el archivo BASE.csv en el botón superior para comenzar.")
