import streamlit as st
import src.agent as agent
import os
import sqlite3
import pandas as pd

from datetime import datetime

DB_PATH = "database.db"

def formatted_monetary_values(valor: float) -> str:
    """
    Formata um número float para uma string no formato de moeda brasileira (R$ 1.234,56).
    """
    us_formatted_value = f"{valor:,.2f}"
    br_formatted_value = us_formatted_value.replace(",", "TEMP").replace(".", ",")
    br_formatted_value = br_formatted_value.replace("TEMP", ".")
    
    return f"R$ {br_formatted_value}"

st.set_page_config(
    page_title="Agente VR/VA",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ Agente Inteligente VR/VA")

with st.sidebar:
    st.image("src/img/Logo_I2A2.png", width=200)
    st.header("ℹ️ Informações")
    st.info("""
    **Como usar:**
    1. Insira sua API Key da OpenAI
    2. Faça upload das planilhas (.xlsx)
    3. Informe a competência
    4. Clique em "Gerar Relatório"
    """)
        

col1, col2 = st.columns([2, 1])

with col1:
    api_key = st.text_input("🔑 API Key OpenAI", type="password", help="Sua chave de API da OpenAI")

with col2:
    competencia = st.text_input(
        "📅 Competência", 
        value=datetime.now().strftime("%m-%Y"),
        placeholder="ex: 05-2025"
    )

st.subheader("📁 Upload de Arquivos")
files = st.file_uploader(
    "Selecione as planilhas (.xlsx)",
    type=["xlsx"],
    accept_multiple_files=True,
    help="Faça upload das planilhas contendo os dados dos funcionários"
)

if files:
    st.success(f"✅ {len(files)} arquivo(s) carregado(s)")
    with st.expander("📋 Ver arquivos carregados"):
        for i, file in enumerate(files, 1):
            file_type = "🔍 Detectando tipo..."
            if 'ativo' in file.name.lower():
                file_type = "Funcionários Ativos"
            elif 'admiss' in file.name.lower():
                file_type = "Admissões"
            elif 'deslig' in file.name.lower():
                file_type = "Desligamentos"
            elif 'rias' in file.name.lower():
                file_type = "Férias"
            elif 'ext' in file.name.lower():
                file_type = "Exterior"
            elif 'est' in file.name.lower():
                file_type = "Estágio"
            elif 'sindicato' in file.name.lower():
                file_type = "Base sindicato x valor"
            elif 'dias' in file.name.lower():
                file_type = "Base dias uteis"
            elif 'afas' in file.name.lower():
                file_type = "Afastamento"
            elif 'apr' in file.name.lower():
                file_type = "Aprendiz"  
            
            st.write(f"{i}. {file.name} ({file.size} bytes) - {file_type}")

# Validações visuais
st.subheader("🔍 Status das Configurações")
col3, col4, col5 = st.columns(3)

with col3:
    if api_key:
        st.success("✅ API Key fornecida")
    else:
        st.error("❌ API Key necessária")

with col4:
    if files:
        if len(files) <= 10:
            st.success(f"✅ {len(files)} arquivo(s) válido(s)")
        else:
            st.error(f"❌ Muitos arquivos ({len(files)}/10)")
    else:
        st.warning("⚠️ Nenhum arquivo carregado")

with col5:
    if competencia:
        st.success("✅ Competência definida")
    else:
        st.warning("⚠️ Competência não definida")

# Botão principal
st.markdown("---")

if st.button("🚀 Gerar Relatório", type="primary", use_container_width=True):
    # Validações
    if not api_key:
        st.error("❌ Informe a API Key da OpenAI!")
    elif not files:
        st.error("❌ Faça upload dos arquivos!")
    elif len(files) > 10:
        st.error(f"❌ Você só pode enviar até 10 arquivos. Você enviou {len(files)}.")
    elif not competencia:
        st.error("❌ Informe a competência!")
    else:
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0, text="🔄 Iniciando...")
            
            try:
                progress_bar.progress(10, text="🤖 Inicializando agente VR/VA...")
                
                if not os.path.exists(DB_PATH):
                    open(DB_PATH, 'a').close()
                
                agente_vrva = agent.VRVAAgent(DB_PATH, api_key)
                
                progress_bar.progress(20, text="📁 Preparando arquivos para processamento...")

                agente_vrva.set_files(files)

                workflow_status = st.empty()
                
                progress_bar.progress(30, text="🔄 Executando workflow LangGraph...")

                initial_state = {
                    'messages': [],
                    'db_path': DB_PATH,
                    'files': files,
                    'competencia': competencia,
                    'current_step': "Iniciando",
                    'processed_files': {},
                    'calculations_done': False,
                    'report_generated': False,
                    'error': ""
                }

                workflow_steps = [
                    ("process_actives", "👥 Processando funcionários ativos", 40),
                    ("process_admissions", "📅 Processando admissões", 50),
                    ("process_fired", "📤 Processando desligamentos", 60),
                    ("process_business_days", "🗓️ Calculando dias úteis", 70),
                    ("process_daily_values", "💰 Calculando valores diários", 80),
                    ("calculate_benefits", "🧮 Calculando benefícios VR/VA", 90),
                    ("generate_report", "📊 Gerando relatório final", 95)
                ]
                
                final_state = agente_vrva.workflow.invoke(initial_state)
                
                for step_name, step_desc, progress_val in workflow_steps:
                    progress_bar.progress(progress_val, text=step_desc)
                    workflow_status.info(f"✅ {step_desc}")
                    
                progress_bar.progress(100, text="✅ Processo finalizado!")
 
                if final_state.get('error'):
                    st.error(f"❌ **Erro no workflow:** {final_state['error']}")
                    
                    with st.expander("🔍 Detalhes do erro"):
                        st.code(final_state['error'])
                        st.write("**Estado final do workflow:**")
                        st.json(final_state)
                
                elif final_state.get('report_generated'):
                    st.success("🎉 **Relatório gerado com sucesso!**")
                    
                    nome_arquivo = f"VR MENSAL {competencia.replace('-', '.')}.xlsx"
                    
                    with st.expander("📊 Detalhes do Processamento"):
                        st.write("**Arquivos processados:**")
                        for file_type, processed in final_state.get('processed_files', {}).items():
                            status = "✅" if processed else "❌"
                            st.write(f"{status} {file_type.title()}")
                        
                        st.write(f"**Último step:** {final_state.get('current_step', 'N/A')}")
                        st.write(f"**Cálculos realizados:** {'✅ Sim' if final_state.get('calculations_done') else '❌ Não'}")

                    if os.path.exists(nome_arquivo):
                        tamanho = os.path.getsize(nome_arquivo) / 1024  # KB
                        
                        st.info(f"""
                            📋 **Detalhes do Relatório VR/VA:**
                            - **Arquivo:** {nome_arquivo}
                            - **Tamanho:** {tamanho:.1f} KB
                            - **Competência:** {competencia}
                            - **Cálculos:** IA Generativa (GPT-4)
                            - **Gerado em:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}

                            🤖 **Cálculos realizados pelo Agente:**
                            - Total VR/VA = Dias úteis × Valor diário
                            - Custo empresa = 80% do total
                            - Desconto funcionário = 20% do total
                            """
                        )
                        
                        # Botão de download
                        with open(nome_arquivo, "rb") as file:
                            st.download_button(
                                label="📥 Baixar Relatório VR/VA",
                                data=file.read(),
                                file_name=nome_arquivo,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                    else:
                        st.warning("⚠️ Arquivo não encontrado após geração")
                        
                        # Verificar outros arquivos Excel no diretório
                        arquivos_excel = [f for f in os.listdir('.') if f.endswith('.xlsx')]
                        if arquivos_excel:
                            st.info("📁 Arquivos Excel encontrados no diretório:")
                            for arquivo in arquivos_excel:
                                if 'relatorio' in arquivo.lower():
                                    with open(arquivo, "rb") as file:
                                        st.download_button(
                                            label=f"📥 Baixar {arquivo}",
                                            data=file.read(),
                                            file_name=arquivo,
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                            use_container_width=True
                                        )
                else:
                    st.error("❌ Falha ao gerar o relatório")
                    st.error("O workflow não foi concluído com sucesso")
                    
                    with st.expander("🔍 Debug - Estado do workflow"):
                        st.json(final_state)
                
                # Mostrar estatísticas finais
                with st.expander("📊 Estatísticas do Processamento"):
                    # Verificar dados na tabela report
                    try:
                        with sqlite3.connect(DB_PATH) as conn:
                            # Verificar se tabela report existe
                            cursor = conn.cursor()
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='report'")
                            if cursor.fetchone():
                                df_stats = pd.read_sql("SELECT COUNT(*) as total_registros FROM report", conn)
                                st.metric("Total de Registros Processados", df_stats['total_registros'].iloc[0])
                                
                                # Estatísticas por estado se existir coluna
                                try:
                                    df_estados = pd.read_sql("""
                                        SELECT ESTADO, COUNT(*) as quantidade 
                                        FROM report 
                                        WHERE ESTADO IS NOT NULL 
                                        GROUP BY ESTADO
                                    """, conn)
                                    if not df_estados.empty:
                                        st.subheader("📍 Distribuição por Estado:")
                                        for _, row in df_estados.iterrows():
                                            st.write(f"• {row['ESTADO']}: {row['quantidade']} funcionários")
                                except Exception:
                                    pass
                                
                                # Totais financeiros se existirem                                
                                try:
                                    df_totais = pd.read_sql("""
                                        SELECT 
                                            SUM(TOTAL) as total,
                                            SUM(CUSTO_EMPRESA) as custo_empresa,
                                            SUM(CUSTO_PROFISSIONAL) as custo_profissionais
                                        FROM report 
                                        WHERE TOTAL IS NOT NULL
                                    """, conn)
                                    
                                    if not df_totais.empty and df_totais['total'].iloc[0]:
                                        st.subheader("💰 Totais Financeiros:")
                                        col_t1, col_t2, col_t3 = st.columns(3)
                                        with col_t1:
                                            total = df_totais['total'].iloc[0] or 0
                                            st.metric("Total VR/VA", formatted_monetary_values(total))
                                        with col_t2:
                                            total_company_cost = df_totais['custo_empresa'].iloc[0] or 0
                                            st.metric("Custo Empresa", formatted_monetary_values(total_company_cost))
                                        with col_t3:
                                            employee_cost = df_totais['custo_profissionais'].iloc[0] or 0
                                            emp_cost = formatted_monetary_values(employee_cost)
                                            st.metric("Desconto Profissional", emp_cost)
                                except Exception:
                                    pass
                            else:
                                st.warning("Tabela 'report' não encontrada no banco")
                    except Exception as e:
                        st.error(f"Erro ao obter estatísticas: {e}")
                
            except Exception as e:
                progress_bar.progress(0, text="❌ Erro durante processamento")
                st.error(f"❌ **Erro durante o processamento:** {str(e)}")
                
                # Mostrar detalhes do erro
                with st.expander("🐛 Detalhes técnicos do erro"):
                    st.code(str(e))
                    
                    # Informações adicionais para debug
                    st.write("**Informações para debug:**")
                    st.write(f"- Banco existe: {os.path.exists(DB_PATH)}")
                    st.write(f"- Número de arquivos: {len(files) if files else 0}")
                    st.write(f"- API Key fornecida: {'Sim' if api_key else 'Não'}")
                    
                    # Tentar mostrar tabelas existentes
                    try:
                        with sqlite3.connect(DB_PATH) as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                            tabelas = [row[0] for row in cursor.fetchall()]
                            st.write(f"- Tabelas no banco: {tabelas}")
                    except Exception:
                        st.write("- Não foi possível verificar tabelas do banco")
                
                st.info("💡 **Dicas para resolver:**")
                st.write("1. Verifique se a API Key da OpenAI está correta")
                st.write("2. Confirme se os arquivos têm as colunas esperadas")
                st.write("3. Verifique se há conexão com internet")
                st.write("4. Consulte os logs no terminal para mais detalhes")
                st.write("5. Certifique-se de que os arquivos contêm dados válidos")

# Footer expandido
st.markdown("---")
st.markdown(
    """
    <div style='text-align: left; color: #666; font-size: 12px;'>
    🤖 <strong>AI-Powered:</strong> OpenAI GPT-4 para cálculos inteligentes<br/>
    🔄 <strong>Workflow:</strong> LangGraph para orquestração estruturada<br/>
    📊 <strong>ETL:</strong> Pandas + SQLite para processamento de dados<br/>
    💻 <strong>Interface:</strong> Streamlit para experiência interativa<br/>
    </div>
    """,
    unsafe_allow_html=True
)
   