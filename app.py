import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard PlanMaster", layout="wide")

# Estilo visual
st.markdown("""
    <style>
        .stApp { background-color: #F8FAF7; }
        div[data-testid="metric-container"] {
            background-color: white;
            border: 1px solid #E2E8F0;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

# 2. O LINK QUE BAIXOU NA ABA ANÓNIMA
LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTrR_UdZ7I9UVMRDX2_JKMCyzPBJW47sJjga5qxvRPBrPStddAamjmTMdDMxnXsITs-mWRXBu29XAHR/pub?output=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    # Lê os dados diretamente do link
    df = pd.read_csv(LINK_CSV)
    # Tenta criar a coluna de vidas (ajusta se o nome for diferente)
    if 'QUAL A QUANTIDADE DE VIDAS?' in df.columns:
        df['vidas_num'] = df['QUAL A QUANTIDADE DE VIDAS?'].astype(str).str.extract('(\d+)').fillna(0).astype(int)
    else:
        df['vidas_num'] = 0
    return df

try:
    df = carregar_dados()
    
    st.title("📊 Dashboard de Leads — PlanMaster")
    
    # 3. CARDS DE MÉTRICAS
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL DE LEADS", len(df))
    c2.metric("TOTAL DE VIDAS", int(df['vidas_num'].sum()))
    c3.metric("MÉDIA VIDAS/LEAD", round(df['vidas_num'].mean(), 1))

    st.divider()

    # 4. GRÁFICOS LADO A LADO
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Operadoras Atuais")
        if 'QUAL O SEU PLANO DE SAÚDE ATUAL?' in df.columns:
            fig = px.bar(df, x='QUAL O SEU PLANO DE SAÚDE ATUAL?', template="plotly_white", color_discrete_sequence=['#0ea5e9'])
            st.plotly_chart(fig, use_container_width=True)
            
    with col2:
        st.subheader("Distribuição de Vidas")
        if 'QUAL A QUANTIDADE DE VIDAS?' in df.columns:
            fig_pie = px.pie(df, names='QUAL A QUANTIDADE DE VIDAS?', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # 5. PLANILHA INTEIRA (O QUE PEDISTE)
    st.divider()
    st.subheader("📋 Base de Dados Completa")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados. Detalhe: {e}")
