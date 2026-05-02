import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO VISUAL (ESTILO CLAUDE)
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
        .stDataFrame { background-color: white; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. SEU LINK DE PUBLICAÇÃO (Ajuste se necessário)
# Cole aqui o link que começa com https://docs.google.com/spreadsheets/d/e/2PACX...
LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTrR_9fI9V_iF3a8E8pM5oN8o_3oB4Y-z_J_z_J_z_J_z_J_z_J_z_J_z_J_z_J_z_J_z_J/pub?output=csv" 

@st.cache_data(ttl=60) # Atualiza rápido para testes
def carregar_dados():
    # Lendo o CSV do Google
    df = pd.read_csv(LINK_CSV)
    
    # TRATAMENTO DE DADOS (Limpando as respostas do Typeform)
    # Extrai apenas o número da coluna de vidas (ex: "2 vidas" vira 2)
    df['vidas_num'] = df['QUAL A QUANTIDADE DE VIDAS?'].astype(str).str.extract('(\d+)').fillna(0).astype(int)
    
    return df

try:
    df = carregar_dados()
    
    st.title("📊 Dashboard de Leads — PlanMaster")
    st.info("Os dados abaixo são atualizados automaticamente a cada novo lead no Typeform.")

    # 3. BLOCO DE MÉTRICAS (IGUAL AO CLAUDE)
    c1, c2, c3, c4 = st.columns(4)
    
    total_leads = len(df)
    total_vidas = df['vidas_num'].sum()
    
    # Filtro para saber quem já tem plano
    com_plano = len(df[df['QUAL O SEU PLANO DE SAÚDE ATUAL?'] != 'NÃO TENHO PLANO DE SAÚDE'])
    percentual_com_plano = int((com_plano / total_leads) * 100) if total_leads > 0 else 0

    c1.metric("TOTAL DE LEADS", total_leads)
    c2.metric("TOTAL DE VIDAS", total_vidas)
    c3.metric("COM PLANO ATUAL", com_plano, f"{percentual_com_plano}%")
    c4.metric("MÉDIA DE VIDAS/LEAD", round(df['vidas_num'].mean(), 1))

    st.write("") # Espaço em branco
    st.divider()

    # 4. GRÁFICOS INTERATIVOS
    col_dir, col_esq = st.columns([2, 1])
    
    with col_dir:
        st.subheader("Operadoras Atuais dos Leads")
        # Gráfico de barras das operadoras
        fig_op = px.bar(
            df, 
            x="QUAL O SEU PLANO DE SAÚDE ATUAL?", 
            template="plotly_white", 
            color_discrete_sequence=['#0ea5e9']
        )
        fig_op.update_layout(xaxis_title=None, yaxis_title="Quantidade")
        st.plotly_chart(fig_op, use_container_width=True)
        
    with col_esq:
        st.subheader("Perfil por Qtd. de Vidas")
        fig_pie = px.pie(
            df, 
            names="QUAL A QUANTIDADE DE VIDAS?", 
            hole=0.4, 
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # 5. PLANILHA INTEIRA (O QUE VOCÊ PEDIU)
    st.divider()
    st.subheader("📋 Base de Dados Completa")
    
    # Barra de busca para a tabela
    busca = st.text_input("🔍 Pesquisar na planilha (Nome, Plano, etc.)")
    
    if busca:
        df_final = df[df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)]
    else:
        df_final = df

    # Exibe a planilha
    st.dataframe(df_final, use_container_width=True)
    
    # Botão para baixar
    st.download_button(
        label="📥 Baixar dados para Excel (CSV)",
        data=df_final.to_csv(index=False).encode('utf-8'),
        file_name='leads_planmaster.csv',
        mime='text/csv',
    )

except Exception as e:
    st.error("⚠️ Erro de Conexão")
    st.write("O Google ainda não autorizou o acesso aos dados. Verifique se o link no código é o mesmo da tela 'Publicar na Web' e se o acesso está como 'Qualquer pessoa com o link'.")
    st.warning(f"Detalhe técnico: {e}")
