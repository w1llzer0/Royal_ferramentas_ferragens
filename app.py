import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="WMS - Royal Ferramentas e Ferragens", layout="wide")

st.title("📦 Sistema WMS - Royal Ferramentas e Ferragens")
st.markdown("---")

# --- GERENCIAMENTO DE ESTOQUE (ESTILO EXCEL EMBUTIDO) ---

# Inicializa um banco de dados de teste idêntico ao que tínhamos feito antes
if "banco_wms" not in st.session_state:
    dados_iniciais = [
        {"Produto": "Chave de Fenda Phillips", "Quantidade": 50, "Preço Unitário (R$)": 15.90, "Tipo": "Entrada"},
        {"Produto": "Martelo Unha 27mm", "Quantidade": 20, "Preço Unitário (R$)": 45.00, "Tipo": "Entrada"},
        {"Produto": "Broca de Aço Rápido 6mm", "Quantidade": 100, "Preço Unitário (R$)": 8.50, "Tipo": "Entrada"},
        {"Produto": "Parafuso Chata 4x40 (Cento)", "Quantidade": 15, "Preço Unitário (R$)": 22.00, "Tipo": "Saída"},
    ]
    st.session_state.banco_wms = pd.DataFrame(dados_iniciais)

# --- CRIAÇÃO DAS ABAS ---
aba1, aba2 = st.tabs(["📋 Planilha & Lançamentos (Estilo Excel)", "📊 Gráficos & Dashboard"])

with aba1:
    st.header("Excel Embutido - Controle Total")
    st.markdown("Edite os valores direto na tabela abaixo, adicione novas linhas ou mude as quantidades como se estivesse no Excel!")
    
    # O editor estilo Excel que você curtiu!
    df_editado = st.data_editor(
        st.session_state.banco_wms,
        num_rows="dynamic", # Permite o cliente clicar em '+' e adicionar linhas novas
        use_container_width=True,
        key="editor_excel"
    )
    
    # Salva automaticamente qualquer alteração feita no "Excel"
    st.session_state.banco_wms = df_editado

with aba2:
    st.header("Dashboard de Movimentações")
    
    df_atual = st.session_state.banco_wms
    
    if df_atual.empty:
        st.info("A planilha está vazia. Insira dados na aba do Excel para gerar os gráficos!")
    else:
        # Força os tipos de dados para os gráficos não quebrarem
        df_atual["Quantidade"] = pd.to_numeric(df_atual["Quantidade"]).fillna(0).astype(int)
        df_atual["Preço Unitário (R$)"] = pd.to_numeric(df_atual["Preço Unitário (R$)"]).fillna(0.0)
        
        # Métricas Rápidas
        col1, col2 = st.columns(2)
        total_itens = df_atual["Quantidade"].sum()
        valor_movimentado = (df_atual["Quantidade"] * df_atual["Preço Unitário (R$)"]).sum()
        
        col1.metric("Total de Itens em Movimento", f"{total_itens} un")
        col2.metric("Valor Total Movimentado", f"R$ {valor_movimentado:,.2f}")
        
        st.markdown("---")
        
        # Gráficos Bonitões Embutidos
        fig = px.bar(
            df_atual,
            x="Produto",
            y="Quantidade",
            color="Tipo",
            title="Volume de Estoque por Produto (Entradas vs Saídas)",
            barmode="group",
            color_discrete_map={"Entrada": "#2ec4b6", "Saída": "#e71d36"}
        )
        
        st.plotly_chart(fig, use_container_width=True)