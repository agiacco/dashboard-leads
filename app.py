import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ESTILO VISUAL "CLAUDE"
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

# 2. SEU LINK QUE FUNCIONOU NA ABA ANÔNIMA
LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTrR_UdZ7l9UVMRDX2_JKMCyzPBJW47sJjga5qxvRPBrPStddAamjmTMdDMxnXsITs-mWRXBu29XAHR/pub?output=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    df = pd.read_csv(LINK_CSV)
    # Criar coluna numérica de vidas
    col_vidas = 'QUAL A QUANTIDADE DE VIDAS?'
    if col_vidas in df.columns:
        df['vidas_num'] = df[col_vidas].astype(str).str.extract('(\d+)').fillna(0).astype(int)
    else:
        df['vidas_num'] = 0
    return df

try:
    df = carregar_dados()
    
    st.title("📊 Dashboard de Leads — PlanMaster")
    st.caption("Sincronizado com sucesso via Google Sheets")

    # 3. CARDS DE MÉTRICAS
    c1, c2, c3, c4 = st.columns(4)
    
    total_leads = len(df)
    total_vidas = df['vidas_num'].sum()
    
    col_plano = 'QUAL O SEU PLANO DE SAÚDE ATUAL?'
    if col_plano in df.columns:
        com_plano = len(df[df[col_plano].astype(str).str.contains('NÃO TENHO', na=False) == False])
    else:
        com_plano = 0
        
    c1.metric("TOTAL DE LEADS", total_leads)
    c2.metric("TOTAL DE VIDAS", int(total_vidas))
    c3.metric("POSSUEM PLANO", com_plano, f"{int((com_plano/total_leads)*100)}%" if total_leads > 0 else "0%")
    c4.metric("MÉDIA VIDAS/LEAD", round(df['vidas_num'].mean(), 1) if total_leads > 0 else 0)

    st.divider()

    # 4. GRÁFICOS
    col_bar, col_pie = st.columns([2, 1])
    
    with col_bar:
        st.subheader("Operadoras Atuais")
        if col_plano in df.columns:
            fig_op = px.bar(df, x=col_plano, template="plotly_white", color_discrete_sequence=['#0ea5e9'])
            st.plotly_chart(fig_op, use_container_width=True)
        
    with col_pie:
        st.subheader("Perfil por Vidas")
        col_vidas = 'QUAL A QUANTIDADE DE VIDAS?'
        if col_vidas in df.columns:
            fig_pie = px.pie(df, names=col_vidas, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

    # 5. TABELA COMPLETA (PLANILHA INTEIRA)
    st.divider()
    st.subheader("📋 Base de Dados Completa")
    busca = st.text_input("🔍 Pesquisar na planilha (Nome, Plano, etc)...")
    
    if busca:
        df_final = df[df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)]
    else:
        df_final = df

    st.dataframe(df_final.drop(columns=['vidas_num'], errors='ignore'), use_container_width=True)

except Exception as e:
    st.error(f"Erro ao processar os dados: {e}")
