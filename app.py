import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="WMS - Royal Ferramentas e Ferragens", layout="wide")

st.title("📦 Sistema WMS - Royal Ferramentas e Ferragens (Modo Local)")
st.markdown("---")

# --- BANCO DE DADOS LOCAL (ARQUIVO CSV) ---
ARQUIVO_BANCO = "banco_dados_wms.csv"

def carregar_dados_local():
    # Se o arquivo não existir, cria um do zero com as colunas certas
    if not os.path.exists(ARQUIVO_BANCO):
        df_vazio = pd.DataFrame(columns=["Produto", "Quantidade", "Preço", "Tipo"])
        df_vazio.to_csv(ARQUIVO_BANCO, index=False)
        return df_vazio
    
    # Se existir, lê o arquivo garantindo os tipos de dados certos
    try:
        df_local = pd.read_csv(ARQUIVO_BANCO)
        df_local["Quantidade"] = pd.to_numeric(df_local["Quantidade"]).fillna(0).astype(int)
        df_local["Preço"] = pd.to_numeric(df_local["Preço"]).fillna(0.0)
        return df_local
    except:
        return pd.DataFrame(columns=["Produto", "Quantidade", "Preço", "Tipo"])

def salvar_dados_local(novo_registro):
    try:
        df_atual = carregar_dados_local()
        df_novo = pd.DataFrame([novo_registro], columns=["Produto", "Quantidade", "Preço", "Tipo"])
        # Junta o novo registro com os antigos e salva no arquivo
        df_final = pd.concat([df_atual, df_novo], ignore_index=True)
        df_final.to_csv(ARQUIVO_BANCO, index=False)
        return True
    except:
        return False

# Inicializa o dataframe com os dados salvos no seu PC
df = carregar_dados_local()

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
                dados_linha = [produto, quantidade, preco, tipo]
                sucesso = salvar_dados_local(dados_linha)
                
                if sucesso:
                    st.success(f"Sucesso! {produto} gravado no banco de dados local!")
                    st.rerun()

with aba2:
    st.header("Análise de Estoque Real")
    
    if df.empty:
        st.info("💡 Nenhum dado cadastrado ainda. Vá na aba '📋 Realizar Lançamento' e faça o primeiro registro para ativar o dashboard!")
    else:
        # Métricas rápidas no topo
        m1, m2 = st.columns(2)
        m1.metric("Total de Itens Movimentados", int(df["Quantidade"].sum()))
        
        valor_total = (df["Quantidade"] * df["Preço"]).sum()
        m2.metric("Valor Total em Movimentações", f"R$ {valor_total:,.2f}")
        
        st.markdown("---")
        st.markdown("### Tabela de Dados Geral")
        st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Gráfico de Movimentações por Produto")
        
        # O gráfico agora roda 100% liso porque os dados locais são controlados direto pelo pandas
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