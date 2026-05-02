import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO ESTILO CLAUDE
st.set_page_config(page_title="Dashboard PlanMaster", layout="wide")

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

# 2. SEU LINK (O QUE VOCÊ JÁ TINHA)
LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQB3jdb7OwrGeYwF2VppIy3MUX-pVpJaelKpwFIOfNHoh0DfbgJ9j1NBypBqfnLBNNHo7cHlwbOncYG/pub?output=csv"

@st.cache_data(ttl=600)
def carregar_dados():
    df = pd.read_csv(LINK_CSV)
    # Ajuste de números para os cálculos
    df['vidas_num'] = df['QUAL A QUANTIDADE DE VIDAS?'].astype(str).str.extract('(\d+)').fillna(0).astype(int)
    return df

try:
    df = carregar_dados()
    
    st.title("📊 Dashboard de Leads — PlanMaster")
    
    # 3. MÉTRICAS (USANDO OS NOMES REAIS DAS SUAS COLUNAS)
    c1, c2, c3, c4 = st.columns(4)
    
    total_leads = len(df)
    total_vidas = df['vidas_num'].sum()
    com_plano = len(df[df['QUAL O SEU PLANO DE SAÚDE ATUAL?'] != 'NÃO TENHO PLANO DE SAÚDE'])
    
    c1.metric("TOTAL DE LEADS", total_leads)
    c2.metric("TOTAL DE VIDAS", int(total_vidas))
    c3.metric("COM PLANO", com_plano, f"{int((com_plano/total_leads)*100)}%")
    c4.metric("SEM PLANO", total_leads - com_plano)

    st.divider()

    # 4. GRÁFICOS
    col_dir, col_esq = st.columns([2, 1])
    
    with col_dir:
        st.subheader("Operadoras Atuais")
        fig = px.bar(df, x="QUAL O SEU PLANO DE SAÚDE ATUAL?", template="plotly_white", color_discrete_sequence=['#0ea5e9'])
        st.plotly_chart(fig, use_container_width=True)
        
    with col_esq:
        st.subheader("Distribuição de Vidas")
        fig_pie = px.pie(df, names="QUAL A QUANTIDADE DE VIDAS?", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    # 5. TABELA COMPLETA (O QUE VOCÊ PEDIU)
    st.subheader("📋 Base de Dados Completa")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados. Verifique a planilha. Detalhe: {e}")
