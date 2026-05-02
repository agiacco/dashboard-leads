import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO "CLAUDE" (CSS)
st.set_page_config(page_title="Dashboard PlanMaster", layout="wide")

st.markdown("""
    <style>
        /* Fundo da página cinza claro */
        .stApp {
            background-color: #F8FAF7;
        }
        /* Estilização dos cards de métricas */
        [data-testid="stMetricValue"] {
            font-size: 32px;
            color: #1E293B;
        }
        div[data-testid="metric-container"] {
            background-color: white;
            border: 1px solid #E2E8F0;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        /* Esconder menu do Streamlit para parecer um site próprio */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM OS DADOS (Link da sua Planilha B em CSV)
# IMPORTANTE: Substitua o link abaixo pelo seu link que termina em output=csv
LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQB3jdb7OwrGeYwF2VppIy3MUX-pVpJaelKpwFIOfNHoh0DfbgJ9j1NBypBqfnLBNNHo7cHlwbOncYG/pub?output=csv"

@st.cache_data(ttl=600) # Atualiza a cada 10 min
def buscar_dados():
    try:
        dados = pd.read_csv(LINK_CSV)
        return dados
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return None

df = buscar_dados()

if df is not None:
    # 3. BARRA LATERAL (FILTROS)
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/pt/2/2b/Logotipo_Bradesco.png", width=150) # Opcional: logo do cliente
    st.sidebar.title("Filtros do Dashboard")
    
    # Filtro de Cliente (Caso tenha abas de clientes diferentes na planilha)
    lista_clientes = df['Cliente'].unique() if 'Cliente' in df.columns else ["PlanMaster"]
    cliente_sel = st.sidebar.selectbox("Selecione o Cliente", lista_clientes)
    
    # Filtro de Mês
    meses_disponiveis = df['Mês/Ano'].unique()
    mes_sel = st.sidebar.selectbox("Mês de Referência", meses_disponiveis)

    # Filtrando os dados baseados na escolha
    df_filtrado = df[(df['Mês/Ano'] == mes_sel)]
    if 'Cliente' in df.columns:
        df_filtrado = df_filtrado[df_filtrado['Cliente'] == cliente_sel]

    # 4. TÍTULO DO DASHBOARD
    st.title(f"Planilha de Leads — {cliente_sel}")
    st.caption(f"Período: {mes_sel} • Dados atualizados via Google Drive")

    st.divider()

    # 5. CARDS DE MÉTRICAS (IGUAL AO CLAUDE)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_leads = len(df_filtrado)
    total_vidas = df_filtrado['Quantidade de vidas'].sum()
    leads_com_plano = len(df_filtrado[df_filtrado['Plano atual'] != 'Sem plano'])
    leads_sem_plano = total_leads - leads_com_plano
    
    # Cálculo Ticket Médio (Lógica: Média da coluna Custo Atual para quem tem plano)
    ticket_medio = df_filtrado[df_filtrado['Plano atual'] != 'Sem plano']['Custo atual'].mean()

    col1.metric("TOTAL DE LEADS", total_leads)
    col2.metric("TOTAL DE VIDAS", f"{int(total_vidas)}")
    col3.metric("COM PLANO", f"{leads_com_plano}", f"{int((leads_com_plano/total_leads)*100)}%")
    col4.metric("SEM PLANO", f"{leads_sem_plano}", f"-{int((leads_sem_plano/total_leads)*100)}%", delta_color="inverse")
    col5.metric("TICKET MÉDIO", f"R$ {ticket_medio:,.2f}")

    st.write("") # Espaçamento

    # 6. GRÁFICOS INTERATIVOS
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Top Operadoras (Plano Atual)")
        # Gráfico de barras empilhadas igual ao pedido
        fig_operadoras = px.bar(
            df_filtrado, 
            x="Plano atual", 
            color="Status", 
            barmode="stack",
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_operadoras.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_operadoras, use_container_width=True)

    with c2:
        st.subheader("Distribuição de Vidas")
        # Contagem de vidas (1 vida, 2 vidas, etc)
        vidas_contagem = df_filtrado['Quantidade de vidas'].value_counts().reset_index()
        vidas_contagem.columns = ['Vidas', 'Qtd Leads']
        
        fig_pizza = px.pie(
            vidas_contagem, 
            values='Qtd Leads', 
            names='Vidas', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    # 7. TABELA DE LEADS RECENTES (OPCIONAL)
    with st.expander("Ver lista completa de leads filtrados"):
        st.dataframe(df_filtrado[['Nome e WhatsApp', 'Plano atual', 'Quantidade de vidas', 'Status']], use_container_width=True)

else:
    st.info("Aguardando carregamento dos dados da Planilha B...")
