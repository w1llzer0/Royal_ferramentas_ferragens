import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# 1. Configuração da página (Tela cheia)
st.set_page_config(layout="wide", page_title="WMS & Dashboard de Ferragens")

ARQUIVO_DADOS = 'dados_vendas_v3.csv'

# --- FUNÇÃO PARA CARREGAR OU CRIAR OS DADOS ---
def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        colunas = ['Data', 'Tipo', 'Cliente', 'Produto', 'Quantidade', 'Valor_Total']
        df = pd.DataFrame(columns=colunas)
        df.to_csv(ARQUIVO_DADOS, index=False)
        return df
    else:
        return pd.read_csv(ARQUIVO_DADOS)

df = carregar_dados()

# --- CORREÇÃO DO BUG DA DATA E RESET DE ID ---
if not df.empty:
    df['Data'] = pd.to_datetime(df['Data'], format='%Y-%m-%d', errors='coerce')
    df['Mes'] = df['Data'].dt.strftime('%m-%b')
    df = df.sort_values(by='Data')
    df = df.reset_index(drop=True)

# --- CRIAÇÃO DAS ABAS ---
aba_operacional, aba_faturamento, aba_cadastro = st.tabs([
    "📦 Controle de Estoque e Entradas", 
    "💰 Inteligência Financeira e Clientes",
    "📝 Lançamentos, Exclusões e Excel"
])

# ==============================================================================
# TAB 1: CONTROLE DE ESTOQUE
# ==============================================================================
with aba_operacional:
    st.title("PAINEL DE ENTRADAS E ESTOQUE")
    st.markdown("---")
    
    if df.empty:
        st.info("👋 Olá! O sistema está limpo. Vá até a aba 'Lançamentos' para alimentar o sistema!")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            data_min = df['Data'].min().date() if not df.empty else datetime.now().date()
            data_max = df['Data'].max().date() if not df.empty else datetime.now().date()
            periodo_sel = st.date_input("Filtrar Período (Início e Fim)", [data_min, data_max])
        with col_f2:
            cliente_sel = st.selectbox("Filtrar por Cliente/Marca", ["Todos"] + list(df['Cliente'].unique()), key="c1")
        with col_f3:
            produto_sel = st.selectbox("Filtrar por Modelo/Produto", ["Todos"] + list(df['Produto'].unique()), key="pr1")
            
        df_filtrado = df.copy()
        if isinstance(periodo_sel, list) and len(periodo_sel) == 2:
            df_filtrado = df_filtrado[(df_filtrado['Data'].dt.date >= periodo_sel[0]) & (df_filtrado['Data'].dt.date <= periodo_sel[1])]
        if cliente_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Cliente'] == cliente_sel]
        if produto_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Produto'] == produto_sel]

        st.markdown("---")
        
        entradas_totais = df_filtrado[df_filtrado['Tipo'] == 'Entrada']['Quantidade'].sum()
        saidas_totais = df_filtrado[df_filtrado['Tipo'] == 'Saída']['Quantidade'].sum()
        saldo_estoque = entradas_totais - saidas_totais
        
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        with col_kpi1: st.metric(label="⬆️ Total de Entradas", value=f"{entradas_totais} un")
        with col_kpi2: st.metric(label="📦 Saldo Atual em Estoque", value=f"{saldo_estoque} un")
        with col_kpi3:
            df_entradas = df_filtrado[df_filtrado['Tipo'] == 'Entrada']
            prod_freq = df_entradas['Produto'].mode()[0] if not df_entradas.empty else "Nenhum"
            st.metric(label="👑 Modelo Mais Frequente", value=prod_freq)
            
        st.markdown("---")
        st.subheader("⚠️ Alertas de Atenção do Estoque")
        
        estoque_por_produto = {}
        for p in df['Produto'].unique():
            ent = df[(df['Produto'] == p) & (df['Tipo'] == 'Entrada')]['Quantidade'].sum()
            sai = df[(df['Produto'] == p) & (df['Tipo'] == 'Saída')]['Quantidade'].sum()
            estoque_por_produto[p] = ent - sai
            
        alertas = [p for p, qtd in estoque_por_produto.items() if qtd < 50]
        if alertas:
            for p in alertas:
                st.error(f"🚨 **CRÍTICO:** O modelo **{p}** está com estoque baixo ({estoque_por_produto[p]} unidades)! Precisa repor.")
        else:
            st.success("✅ Todos os modelos estão com níveis estáveis de estoque (acima de 50 un).")
            
        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Ranking de Modelos mais Movimentados")
            df_rank = df_filtrado.groupby(['Produto', 'Tipo'])['Quantidade'].sum().reset_index()
            fig_bar = px.bar(df_rank, x='Quantidade', y='Produto', color='Tipo', barmode='group', orientation='h', template="plotly_white")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.subheader("Linha de Tempo de Movimentações")
            df_tempo = df_filtrado.groupby(['Data', 'Tipo'])['Quantidade'].sum().reset_index()
            fig_line = px.line(df_tempo, x='Data', y='Quantidade', color='Tipo', markers=True, template="plotly_white")
            st.plotly_chart(fig_line, use_container_width=True)

# ==============================================================================
# TAB 2: INTELIGÊNCIA FINANCEIRA
# ==============================================================================
with aba_faturamento:
    st.title("💰 Análise de Faturamento & Recomendações")
    st.markdown("---")
    
    if df.empty:
        st.info("Nenhum dado financeiro disponível ainda.")
    else:
        df_vendas = df[df['Tipo'] == 'Saída']
        
        if df_vendas.empty:
            st.info("📉 Nenhuma venda (Saída) registrada para calcular faturamento ainda.")
        else:
            st.subheader("Faturamento Mensal Realizado (Vendas de Saída em R$)")
            df_fat_mes = df_vendas.groupby('Mes')['Valor_Total'].sum().reset_index().sort_values(by='Mes')
            fig_fat = px.bar(df_fat_mes, x='Mes', y='Valor_Total', text_auto='.2f', color_discrete_sequence=['#2ecc71'], template="plotly_white")
            st.plotly_chart(fig_fat, use_container_width=True)
            
            st.markdown("---")
            col_fat1, col_fat2 = st.columns(2)
            
            with col_fat1:
                st.subheader("Histórico do Cliente")
                cliente_foco = st.selectbox("Selecione um Cliente", df_vendas['Cliente'].unique())
                df_cliente = df_vendas[df_vendas['Cliente'] == cliente_foco]
                total_gasto = df_cliente['Valor_Total'].sum()
                st.markdown(f"O cliente **{cliente_foco}** já comprou um total de **R$ {total_gasto:,.2f}**.")
                
                if not df_cliente.empty:
                    prod_top_cliente = df_cliente.groupby('Produto')['Quantidade'].sum().idxmax()
                    st.info(f"📦 **Produto mais comprado por ele:** {prod_top_cliente}")

            with col_fat2:
                st.subheader("💡 O que oferecer para esse cliente?")
                produtos_do_cliente = set(df_cliente['Produto'].unique())
                todos_produtos_venda = set(df_vendas['Produto'].unique())
                produtos_nao_comprados = todos_produtos_venda - produtos_do_cliente
                
                if produtos_nao_comprados:
                    st.warning("Este cliente ainda não comprou os seguintes itens:")
                    for prod in produtos_nao_comprados: st.markdown(f"* **{prod}**")
                else:
                    st.success("🔥 Esse cliente já consome todos os produtos!")

# ==============================================================================
# TAB 3: TELA DE LANÇAMENTOS, EXCLUSÕES E EXCEL (O UPGRADE!)
# ==============================================================================
with aba_cadastro:
    col_cadastro_form, col_exclusao_form = st.columns([2, 1])
    
    # --- FORMULÁRIO DE CADASTRO MANUAL ---
    with col_cadastro_form:
        st.subheader("📝 Novo Lançamento Manual")
        with st.form("form_cadastro_turbinado", clear_on_submit=True):
            col_in1, col_in2 = st.columns(2)
            
            with col_in1:
                nova_data = st.date_input("Data do Lançamento", datetime.now())
                novo_tipo = st.radio("Tipo de Operação", ["Entrada", "Saída"])
                
                modo_cliente = st.radio("Cliente/Marca:", ["Escolher Existente", "Cadastrar Novo"], horizontal=True)
                if modo_cliente == "Escolher Existente" and not df.empty and len(df['Cliente'].unique()) > 0:
                    novo_cliente = st.selectbox("Selecione", df['Cliente'].unique())
                else:
                    novo_cliente = st.text_input("Digite o nome do NOVO Cliente")
                    
            with col_in2:
                nova_qtd = st.number_input("Quantidade de Unidades", min_value=1, step=1)
                novo_valor = st.number_input("Valor Financeiro Total (R$)", min_value=0.0, step=10.0)
                
                modo_produto = st.radio("Produto/Modelo:", ["Escolher Existente", "Cadastrar Novo"], horizontal=True)
                if modo_produto == "Escolher Existente" and not df.empty and len(df['Produto'].unique()) > 0:
                    novo_produto = st.selectbox("Selecione o Produto/Modelo", df['Produto'].unique())
                else:
                    novo_produto = st.text_input("Digite o nome do NOVO Produto/Modelo")
                    
            botao_salvar = st.form_submit_button("💾 Confirmar Lançamento Manual")
            
            if botao_salvar:
                if novo_cliente == "" or novo_produto == "":
                    st.error("❌ Erro! Preencha os campos antes de confirmar.")
                else:
                    data_formatada = nova_data.strftime('%Y-%m-%d')
                    nova_linha = pd.DataFrame([{
                        'Data': data_formatada,
                        'Tipo': novo_tipo,
                        'Cliente': novo_cliente,
                        'Produto': novo_produto,
                        'Quantidade': int(nova_qtd),
                        'Valor_Total': float(novo_valor)
                    }])
                    
                    nova_linha.to_csv(ARQUIVO_DADOS, mode='a', header=False, index=False)
                    st.success(f"✅ {novo_tipo} registrada!")
                    st.rerun()

    # --- FORMULÁRIO DE EXCLUSÃO SEGURO ---
    with col_exclusao_form:
        st.subheader("🗑️ Corrigir Erro / Excluir")
        
        if df.empty:
            st.write("Nenhum dado para excluir.")
        else:
            opcoes_exclusao = {}
            for idx, row in df.iterrows():
                data_str = pd.to_datetime(row['Data']).strftime('%d/%m')
                texto_exibicao = f"ID {idx} | {data_str} - {row['Tipo']} - {row['Cliente']} ({row['Produto']})"
                opcoes_exclusao[texto_exibicao] = idx
            
            with st.form("form_exclusao_seguro", clear_on_submit=True):
                selecionado = st.selectbox("Selecione o registro exato para deletar:", list(opcoes_exclusao.keys()))
                id_para_deletar = opcoes_exclusao[selecionado]
                
                botao_deletar = st.form_submit_button("❌ Apagar Registro Selecionado")
                
                if botao_deletar:
                    df_novo = df.drop(index=id_para_deletar)
                    df_novo['Data'] = df_novo['Data'].dt.strftime('%Y-%m-%d')
                    df_novo = df_novo.drop(columns=['Mes'])
                    df_novo.to_csv(ARQUIVO_DADOS, index=False)
                    st.success("💥 Registro removido com sucesso!")
                    st.rerun()

    # ==============================================================================
    # --- NOVO BLOCO: IMPORTAÇÃO EM MASSA VIA PLANILHA (EXCEL / CSV) ---
    # ==============================================================================
    st.markdown("---")
    st.subheader("🚀 Importação em Massa via Planilha (Excel ou CSV)")
    
    col_xlsx1, col_xlsx2 = st.columns([1, 2])
    
    with col_xlsx1:
        st.markdown("**Passo 1: Baixe o modelo padrão**")
        # Criamos o modelo ideal para o cliente não errar as colunas
        modelo_estrutura = pd.DataFrame(columns=['Data', 'Tipo', 'Cliente', 'Produto', 'Quantidade', 'Valor_Total'])
        # Exemplo preenchido fictício na primeira linha para ele entender
        modelo_estrutura.loc[0] = ['2026-07-08', 'Entrada', 'Fornecedor Central', 'Parafuso Philips', 100, 150.00]
        
        csv_modelo = modelo_estrutura.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Planilha Modelo (Excel/CSV)",
            data=csv_modelo,
            file_name="modelo_carga_estoque.csv",
            mime="text/csv",
            help="Abra essa planilha no Excel, preencha as linhas com seus produtos e salve!"
        )

    with col_xlsx2:
        st.markdown("**Passo 2: Arrasta a planilha preenchida aqui**")
        arquivo_enviado = st.file_uploader("Escolha o arquivo CSV preenchido", type=["csv"])
        
        if arquivo_enviado is not None:
            try:
                # Lê a planilha que o cliente enviou
                df_importado = pd.read_csv(arquivo_enviado)
                
                # Validação rápida de segurança para ver se ele não alterou as colunas obrigatórias
                colunas_obrigatorias = ['Data', 'Tipo', 'Cliente', 'Produto', 'Quantidade', 'Valor_Total']
                if all(col in df_importado.columns for col in colunas_obrigatorias):
                    
                    if st.button("🔥 Confirmar Carga de Todos os Produtos"):
                        # Junta os dados importados com a base permanente do sistema
                        df_importado.to_csv(ARQUIVO_DADOS, mode='a', header=False, index=False)
                        st.success(f"🎉 Sucesso! {len(df_importado)} novos registros foram importados em bloco de uma só vez!")
                        st.rerun()
                else:
                    st.error("❌ Erro! A planilha enviada não possui as colunas corretas. Use o modelo padrão.")
            except Exception as e:
                st.error(f"❌ Erro ao ler o arquivo: {e}")

    st.markdown("---")
    st.subheader("📋 Tabela Geral de Dados (`dados_vendas_v3.csv`)")
    if df.empty:
        st.text("Nenhum histórico gravado até o momento.")
    else:
        st.dataframe(df, use_container_width=True)