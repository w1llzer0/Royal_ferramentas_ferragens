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
@st.cache_data(ttl=5)
def carregar_dados_google():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo ID único
        planilha = client.open_by_key("1bDvziHPQ5KDYm_1SGJ8hK5CVHMEfELHlyNlDndv2gfs").sheet1
        
        todas_linhas = planilha.get_all_values()
        
        if len(todas_linhas) <= 1:
            return pd.DataFrame(columns=["Produto", "Quantidade", "Preço", "Tipo"])
            
        # Cria o DataFrame usando a primeira linha como cabeçalho
        df_sheets = pd.DataFrame(todas_linhas[1:], columns=todas_linhas[0])
        
        # Remove linhas onde o nome do produto está totalmente vazio (limpa linhas fantasmas)
        df_sheets = df_sheets[df_sheets["Produto"].str.strip() != ""]
        
        if df_sheets.empty:
            return pd.DataFrame(columns=["Produto", "Quantidade", "Preço", "Tipo"])

        # FORÇA A CONVERSÃO RESTRITA PARA NÚMEROS
        df_sheets["Quantidade"] = pd.to_numeric(df_sheets["Quantidade"], errors='coerce').fillna(0).astype(int)
        df_sheets["Preço"] = pd.to_numeric(df_sheets["Preço"], errors='coerce').fillna(0.0)
        
        return df_sheets
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {e}")
        return pd.DataFrame(columns=["Produto", "Quantidade", "Preço", "Tipo"])

def salvar_dados_google(novo_registro):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        planilha = client.open_by_key("1bDvziHPQ5KDYm_1SGJ8hK5CVHMEfELHlyNlDndv2gfs").sheet1
        
        if len(planilha.get_all_values()) == 0:
            planilha.append_row(["Produto", "Quantidade", "Preço", "Tipo"])
            
        planilha.append_row(novo_registro)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar na planilha: {e}")
        return False

# Executa a carga dos dados
df = carregar_dados_google()

# --- CRIAÇÃO DAS ABAS NA TELA ---
aba1, aba2 = st.tabs(["📋 Realizar Lançamento", "📊 Dashboard & Estoque"])

with aba1:
    st.header("Novo Registro de Estoque")
    
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
                dados_linha = [produto, str(quantidade), str(preco), tipo]
                sucesso = salvar_dados_google(dados_linha)
                
                if sucesso:
                    st.success(f"Sucesso! {produto} gravado direto no Google Sheets!")
                    st.cache_data.clear()
                    st.rerun()

with aba2:
    st.header("Análise de Estoque Real")
    
    # Valida se o DataFrame realmente tem dados válidos para exibir
    if df.empty or df["Produto"].isna().all():
        st.info("Nenhum dado válido encontrado no Google Sheets. Faça um lançamento válido para gerar os gráficos!")
    else:
        # Métricas rápidas
        m1, m2 = st.columns(2)
        m1.metric("Total de Itens Movimentados", int(df["Quantidade"].sum()))
        
        valor_total = (df["Quantidade"] * df["Preço"]).sum()
        m2.metric("Valor Total em Movimentações", f"R$ {valor_total:,.2f}")
        
        st.markdown("---")
        st.markdown("### Tabela de Dados Geral (Google Sheets)")
        st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Gráfico de Movimentações por Produto")
        
        # Filtra apenas linhas que têm quantidade maior que zero para o gráfico não quebrar
        df_grafico = df[df["Quantidade"] > 0]
        
        if not df_grafico.empty:
            fig = px.bar(
                df_grafico, 
                x="Produto", 
                y="Quantidade", 
                color="Tipo", 
                title="Quantidade Movimentada por Item",
                barmode="group",
                color_discrete_map={"Entrada": "#2ec4b6", "Saída": "#e71d36"}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Dados numéricos insuficientes na planilha para renderizar o gráfico.")