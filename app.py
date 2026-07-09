import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="WMS - Royal Ferramentas e Ferragens", layout="wide")

st.title("📦 Sistema WMS - Royal Ferramentas e Ferragens")
st.markdown("---")

# --- CONEXÃO COM O GOOGLE SHEETS ---
@st.cache_data(ttl=10)  # Atualiza os dados a cada 10 segundos se houver recarregamento
def carregar_dados_google():
    try:
        # Define os escopos de acesso
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Puxa as credenciais de forma segura dos Secrets do Streamlit Cloud
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo nome exato
        planilha = client.open("Banco_Dados_WMS").sheet1
        
        # Pega todas os registros da planilha
        registros = planilha.get_all_records()
        
        if not registros:
            # Se a planilha estiver totalmente vazia, cria um DataFrame com as colunas padrão
            return pd.DataFrame(columns=["Produto", "Quantidade", "Preço", "Tipo"])
            
        return pd.DataFrame(registros)
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {e}")
        return pd.DataFrame(columns=["Produto", "Quantidade", "Preço", "Tipo"])

def salvar_dados_google(novo_registro):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        planilha = client.open("Banco_Dados_WMS").sheet1
        
        # Se a planilha estiver vazia (sem cabeçalhos), adiciona os cabeçalhos primeiro
        if len(planilha.get_all_values()) == 0:
            planilha.append_row(["Produto", "Quantidade", "Preço", "Tipo"])
            
        planilha.append_row(novo_registro)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar na planilha: {e}")
        return False

# Carrega o DataFrame vindo da nuvem do Google
df = carregar_dados_google()

# --- ABA DE LANÇAMENTOS E VISUALIZAÇÃO ---
aba1, aba2 = st.tabs(["📋 Realizar Lançamento", "📊 Dashboard & Estoque"])

with aba1:
    st.header("Novo Registro de Estoque")
    
    # Formulário de entrada de dados
    with st.form("form_wms", clear_on_submit=True):
        produto = st.text_input("Descrição / Nome do Produto:")
        quantidade = st.number_input("Quantidade:", min_value=1, step=1)
        preco = st.number_input("Preço Unitário (R$):", min_value=0.0, step=0.01)
        tipo = st.selectbox("Tipo de Operação:", ["Entrada", "Saída"])
        
        botao_enviar = st.form_submit_button("Gravar no Estoque")
        
        if botao_enviar:
            if produto.strip() == "":
                st.warning("Por favor, digite o nome do produto.")
            else:
                # Cria a lista com os dados na ordem correta da planilha
                dados_linha = [produto, quantidade, preco, tipo]
                
                # Executa a função de salvamento na nuvem do Google
                sucesso = salvar_dados_google(dados_linha)
                
                if sucesso:
                    st.success(f"Sucesso! {produto} gravado direto no Google Sheets!")
                    # Limpa o cache para forçar o sistema a puxar os dados atualizados
                    st.cache_data.clear()
                    st.rerun()

with aba2:
    st.header("Análise de Estoque Real")
    
    if df.empty:
        st.info("Nenhum dado encontrado no Google Sheets. Faça o primeiro lançamento para gerar os gráficos!")
    else:
        # Garante a tipagem correta das colunas numéricas
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors='coerce').fillna(0)
        df["Preço"] = pd.to_numeric(df["Preço"], errors='coerce').fillna(0.0)
        
        # Cria colunas de métricas rápidas no topo
        m1, m2 = st.columns(2)
        m1.metric("Total de Itens Movimentados", int(df["Quantidade"].sum()))
        m2.metric("Valor Total em Movimentações", f"R$ {df['Quantidade'].sum() * df['Preço'].mean():,.2f}")
        
        st.markdown("### Tabela de Dados Geral (Google Sheets)")
        st.dataframe(df, use_container_width=True)
        
        # Gráfico Dinâmico usando o Plotly
        st.markdown("### Gráfico de Movimentações por Produto")
        fig = px.bar(
            df, 
            x="Produto", 
            y="Quantidade", 
            color="Tipo", 
            title="Quantidade Movimentada por Item",
            barmode="group",
            color_discrete_map={"Entrada": "#2ec4b6", "Saída": "#e71d36"}
        )
        st.plotly_chart(fig, use_container_width=True)