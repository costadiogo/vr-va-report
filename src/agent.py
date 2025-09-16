import re
import unicodedata
import sqlite3
import pandas as pd

from typing import Dict, Any, List, Optional, Union
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain.prompts import PromptTemplate

from src.tools.admission_tool import process_admissions
from src.tools.actives_tool import process_actives
from src.tools.dismissed_tool import process_fired
from src.tools.business_days_tool import process_business_days
from src.tools.union_value_tool import process_daily_values
from src.tools.vacation_tool import process_vacation
from src.logger.logger import logger

# ==============================
# STATE
# ==============================
class VRVAState(TypedDict):
    """Estado do workflow LangGraph"""
    messages: Annotated[list, add_messages]
    db_path: str
    files: List[Any]
    competencia: str
    current_step: str
    processed_files: Dict[str, bool]
    calculations_done: bool
    report_generated: bool
    error: str

# ==============================
# VRVA AGENT
# ==============================
class VRVAAgent:
    def __init__(self, db_path: str, openai_api_key: str):
        logger.info("🚀 Inicializando VRVA Agent")

        self.db_path = db_path
        self.openai_api_key = openai_api_key

        self.files: List[Any] = []

        self.llm = ChatOpenAI(
            temperature=0,
            api_key=openai_api_key,
            model="gpt-4",
            max_tokens=3000,
            verbose=True
        )

        self.calculation_prompt = PromptTemplate(
            input_variables=["competencia", "table_info", "sample_data"],
            template="""
                Você é um especialista em cálculos de benefícios VR/VA (Vale Refeição/Vale Alimentação).

                CONTEXTO:
                - Competência: {competencia}
                - Tabela 'report' já contém dados do ETL.
                - Considere a data de 15/04/2025 a 15/05/2025 para todos os cálculos.

                CÁLCULOS NECESSÁRIOS:
                1. TOTAL = COALESCE(DIAS_UTEIS,0) * COALESCE(VALOR_DIARIO,0)
                2. CUSTO_EMPRESA = TOTAL * 0.80
                3. CUSTO_PROFISSIONAL = TOTAL * 0.20
                4. OBS_GERAL = 
                   - Se DATA_DEMISSAO <= dia 15 → "Desligamento até dia 15 - Verificar elegibilidade"
                   - Se DATA_DEMISSAO > dia 15 → "Desligamento após dia 15 - Valor proporcional"
                   - Se ADMISSAO no mesmo mês da competência → "Admissão no mês - Valor proporcional"
                   - Se DIAS_UTEIS != (21, 22) → "Férias - Valor proporcional"
                   - Caso contrário → "Funcionário ativo - Valor integral"

                INSTRUÇÃO:
                - Gere comandos SQL UPDATE para atualizar a tabela 'report'. Apenas UPDATEs na tabela 'report'.
                - Sempre use ROUND(valor, 2).
                - Trate valores NULL como 0.
                - Gere **apenas** SQL válido, sem explicações.

                Estrutura da tabela:
                {table_info}

                Exemplo de dados:
                {sample_data}
            """
        )

        self.workflow = self._build_workflow()

        logger.info("✅ VRVA Agent pronto para execução.")

    # ==============================
    # WORKFLOW
    # ==============================
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(VRVAState)

        workflow.add_node("process_actives", self.process_actives_node)
        workflow.add_node("process_admissions", self.process_admissions_node)
        workflow.add_node("process_fired", self.process_fired_node)
        workflow.add_node("process_business_days", self.process_business_days_node)
        workflow.add_node("process_daily_values", self.process_daily_values_node)
        workflow.add_node("process_vacation_days", self.process_vacation_days_node)
        workflow.add_node("calculate_benefits", self.calculate_benefits_node)
        workflow.add_node("generate_report", self.generate_report_node)

        workflow.set_entry_point("process_actives")
        workflow.add_edge("process_actives", "process_admissions")
        workflow.add_edge("process_admissions", "process_fired")
        workflow.add_edge("process_fired", "process_business_days")
        workflow.add_edge("process_business_days", "process_daily_values")
        workflow.add_edge("process_daily_values", "process_vacation_days")
        workflow.add_edge("process_vacation_days", "calculate_benefits")
        workflow.add_edge("calculate_benefits", "generate_report")
        workflow.add_edge("generate_report", END)

        return workflow.compile()

    # ==============================
    # WORKFLOW NODES
    # ==============================
    def process_actives_node(self, state: VRVAState) -> VRVAState:
        try:
            df = self._find_and_load_file(state.get("files", None) or self.files, "ativos")
            if df is None or df.empty:
                raise ValueError("Arquivo de ativos não encontrado.")
            process_actives(state["db_path"], df)
            state["processed_files"]["actives"] = True
            state["current_step"] = "Ativos processados"
            logger.info("Ativos processados com sucesso.")
        except Exception as e:
            logger.exception("Erro ao processar ativos")
            state["error"] = f"Erro ao processar ativos: {e}"
        return state

    def process_admissions_node(self, state: VRVAState) -> VRVAState:
        try:
            df_admissions = self._find_and_load_file(state.get("files", None) or self.files, "admissao")
            df_actives = self._find_and_load_file(state.get("files", None) or self.files, "ativos")
            if df_admissions is not None and not df_admissions.empty and df_actives is not None and not df_actives.empty:
                process_admissions(state["db_path"], df_admissions, df_actives)
                state["processed_files"]["admissions"] = True
                logger.info("Admissões processadas com sucesso.")
            else:
                logger.warning("Nenhum arquivo de admissões encontrado. Pulando.")
            state["current_step"] = "Admissões processadas"
        except Exception as e:
            logger.exception("Erro ao processar admissões")
            state["error"] = f"Erro ao processar admissões: {e}"
        return state

    def process_fired_node(self, state: VRVAState) -> VRVAState:
        try:
            df = self._find_and_load_file(state.get("files", None) or self.files, "desligados")
            if df is not None and not df.empty:
                process_fired(state["db_path"], df)
                state["processed_files"]["fired"] = True
                logger.info("Desligamentos processados com sucesso.")
            else:
                logger.warning("Nenhum arquivo de desligados encontrado. Pulando.")
            state["current_step"] = "Desligamentos processados"
        except Exception as e:
            logger.exception("Erro ao processar desligamentos")
            state["error"] = f"Erro ao processar desligamentos: {e}"
        return state

    def process_business_days_node(self, state: VRVAState) -> VRVAState:
        try:
            process_business_days(state["db_path"])
            state["processed_files"]["business_days"] = True
            state["current_step"] = "Dias úteis processados"
            logger.info("Dias úteis processados com sucesso.")
        except Exception as e:
            logger.exception("Erro ao processar dias úteis")
            state["error"] = f"Erro ao processar dias úteis: {e}"
        return state

    def process_daily_values_node(self, state: VRVAState) -> VRVAState:
        try:
            process_daily_values(state["db_path"])
            state["processed_files"]["daily_values"] = True
            state["current_step"] = "Valores diários processados"
            logger.info("Valores diários processados com sucesso.")
        except Exception as e:
            logger.exception("Erro ao processar valores diários")
            state["error"] = f"Erro ao processar valores diários: {e}"
        return state
    
    def process_vacation_days_node(self, state: VRVAState) -> VRVAState:
        try:
            df = self._find_and_load_file(state.get("files", None) or self.files, "férias")
            if df is not None and not df.empty:
                process_vacation(state["db_path"], df)
                state["processed_files"]["vacation"] = True
                logger.info("Ferias processados com sucesso.")
            else:
                logger.warning("Nenhum arquivo de férias encontrado. Pulando.")
            state["current_step"] = "Férias processados"
        except Exception as e:
            logger.exception("Erro ao processar férias")
            state["error"] = f"Erro ao processar férias: {e}"
        return state

    def calculate_benefits_node(self, state: VRVAState) -> VRVAState:
        try:
            if not self._table_exists(state["db_path"], "report"):
                raise ValueError("Tabela 'report' não existe. ETL não criou a tabela corretamente.")

            table_info = self._get_table_structure()
            sample_data = self._get_sample_data()

            prompt = self.calculation_prompt.format(
                competencia=state["competencia"],
                table_info=table_info,
                sample_data=sample_data
            )

            response = self.llm.invoke([HumanMessage(content=prompt)])
            sql_commands = self._extract_sql_from_response(response.content)

            if not sql_commands:
                raise ValueError("LLM não retornou comandos UPDATE válidos.")

            self._execute_sql_commands(state["db_path"], sql_commands)

            state["calculations_done"] = True
            state["current_step"] = "Cálculos concluídos"
            logger.info("Cálculos via LLM aplicados com sucesso.")
        except Exception as e:
            logger.exception("Erro nos cálculos via LLM")
            state["error"] = f"Erro nos cálculos via LLM: {e}"
        return state

    def generate_report_node(self, state: VRVAState) -> VRVAState:
        try:
            if not self._table_exists(state["db_path"], "report"):
                raise ValueError("Tabela report não existe. Processo ETL falhou.")

            with sqlite3.connect(state["db_path"]) as conn:
                df_final = pd.read_sql("SELECT * FROM report", conn)              


            if df_final.empty:
                raise ValueError("Tabela report está vazia.")

            filename = f"VR MENSAL {state['competencia'].replace('-', '.')}.xlsx"
            self._save_excel_report(df_final, filename, state["competencia"])

            state["report_generated"] = True
            state["current_step"] = f"Relatório gerado: {filename}"
            logger.info("Relatório gerado com sucesso: %s", filename)
        except Exception as e:
            logger.exception("Erro ao gerar relatório")
            state["error"] = f"Erro ao gerar relatório: {e}"
        return state

    # ==============================
    # SAVE REPORT
    # ==============================
    def formatted_monetary_values(self, valor: float) -> str:
        """
        Formata um número float para uma string no formato de moeda brasileira (R$ 1.234,56).
        """
        us_formatted_value = f"{valor:,.2f}"
        br_formatted_value = us_formatted_value.replace(",", "TEMP").replace(".", ",")
        br_formatted_value = br_formatted_value.replace("TEMP", ".")
        
        return f"R$ {br_formatted_value}"

    def _save_excel_report(self, df: pd.DataFrame, filename: str, competencia: str):
        df_report = df.copy()
        df_report.insert(0, "COMPETENCIA", competencia)

        column_mapping = {
            "COMPETENCIA": "Competência",
            "MATRICULA": "Matrícula",
            "SINDICATO": "Sindicato do Colaborador",
            "ADMISSAO": "Admissão",
            "DIAS_UTEIS": "Dias",
            "VALOR_DIARIO": "VALOR DIÁRIO VR",
            "TOTAL": "TOTAL",
            "CUSTO_EMPRESA": "Custo empresa",
            "CUSTO_PROFISSIONAL": "Desconto profissional",
            "OBS_GERAL": "OBS GERAL",
        }
        df_report.rename(columns={k: v for k, v in column_mapping.items() if k in df_report.columns}, inplace=True)

        columns_to_format = [
            "VALOR DIÁRIO VR",
            "TOTAL",
            "Custo empresa",
            "Desconto profissional"
        ]

        for col in columns_to_format:
            if col in df_report.columns:
                df_report[col] = df_report[col].apply(self.formatted_monetary_values)
        
        columns_order = [
            "Matrícula",
            "Admissão",
            "Sindicato do Colaborador",
            "Competência",
            "Dias",
            "VALOR DIÁRIO VR",
            "TOTAL",
            "Custo empresa",
            "Desconto profissional",
            "OBS GERAL"
        ]
                
        total_company_cost = df.get("CUSTO_EMPRESA", pd.Series([0], dtype=float)).sum()
        employee_cost = df.get("CUSTO_PROFISSIONAL", pd.Series([0], dtype=float)).sum()
        total = df.get("TOTAL", pd.Series([0], dtype=float)).sum()

        colunas_finais_existentes = [col for col in columns_order if col in df_report.columns]
        
        df_report_complete = df_report[colunas_finais_existentes]
        
        summary = {
            "Total Custo Empresa (R$)": self.formatted_monetary_values(total_company_cost),
            "Total Colaboradores (R$)": self.formatted_monetary_values(employee_cost),
            "Total Geral (R$)": self.formatted_monetary_values(total)
        }
        
        df_summary = pd.DataFrame([summary])

        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df_report_complete.to_excel(writer, sheet_name="Relatorio", index=False)
            df_summary.to_excel(writer, sheet_name="Custos totais", index=False)

    # ==============================
    # HELPERS (SQL / LLM / FILES)
    # ==============================
    def _get_table_structure(self) -> str:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(report)")
                cols = cursor.fetchall()
                cursor.execute("SELECT COUNT(*) FROM report")
                total = cursor.fetchone()[0]
            return f"TOTAL DE REGISTROS: {total}\n" + "\n".join([f"- {c[1]} ({c[2]})" for c in cols])
        except Exception as e:
            logger.warning("Tabela report não disponível ao obter estrutura: %s", e)
            return "Tabela report não existe ou inacessível."

    def _get_sample_data(self) -> str:
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql("SELECT * FROM report LIMIT 3", conn)
            return df.to_string(index=False) if not df.empty else "Nenhum dado encontrado"
        except Exception as e:
            logger.warning("Não foi possível obter amostra da tabela report: %s", e)
            return "Nenhum dado encontrado"

    def _extract_sql_from_response(self, response: str) -> List[str]:
        text = response.replace("```sql", "").replace("```", "")

        commands = []
        for part in text.split(";"):
            part = part.strip()
            if not part:
                continue
            up = part.upper()
            if up.startswith("UPDATE") and "REPORT" in up:

                commands.append(part + ";")
        return commands

    def _execute_sql_commands(self, db_path: str, commands: List[str]):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for cmd in commands:
                try:
                    logger.info("Executando SQL: %s", cmd)
                    cursor.execute(cmd)
                except Exception as e:
                    logger.error("Erro ao executar SQL '%s': %s", cmd, e)
            conn.commit()

    def _normalize_text(self, text: str) -> str:
        """Converte para minúsculas, remove acentos e caracteres não alfanuméricos."""
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'[^a-z0-9]', '', text.lower())
    
    def _find_and_load_file(self, files_or_state: Optional[Union[List[Any], VRVAState]], file_type: str) -> pd.DataFrame:
        """Localiza e carrega arquivo com base em padrões, usando nomes normalizados"""
        patterns = {
            "ativos": ["ativos", "ativo", "active", "funcionarios"],
            "admissao": ["admissao", "admission", "admitidos"],
            "desligados": ["desligados", "deslig", "fired", "demitidos", "demit"],
            "ferias": ["ferias", "feria", "feri"]
        }

        files = []
        if isinstance(files_or_state, dict):
            files = files_or_state.get("files", []) or []
        elif isinstance(files_or_state, list):
            files = files_or_state
        else:
            files = self.files

        normalized_type = self._normalize_text(file_type)
        search_patterns = [self._normalize_text(p) for p in patterns.get(normalized_type, [normalized_type])]

        for file in files:
            try:
                original_name = getattr(file, "name", str(file))
                normalized_name = self._normalize_text(original_name)

                if any(p in normalized_name for p in search_patterns):
                    logger.info(f"✅ Arquivo encontrado para '{file_type}': {original_name}")
                    try:
                        df = pd.read_excel(file)
                        return df
                    except Exception as e:
                        logger.error(f"Erro ao ler o arquivo {original_name}: {e}")
                        return pd.DataFrame()
            except Exception as e:
                logger.error(f"Erro ao processar o nome de um arquivo: {e}")
        
        logger.warning(f"⚠️ Nenhum arquivo encontrado para o tipo '{file_type}' com os padrões {search_patterns}")
        return pd.DataFrame()

    def set_files(self, files: List[Any]):
        """Define arquivos para processamento."""
        self.files = files
        logger.info("Arquivos definidos: %s", [getattr(f, "name", str(f)) for f in files])

    def _table_exists(self, db_path: str, table_name: str) -> bool:
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error("Erro ao verificar existência de tabela: %s", e)
            return False

    # ==============================
    # EXECUÇÃO DO WORKFLOW
    # ==============================
    def build_excel_report(self, competencia: str) -> bool:
        """Executa o workflow completo"""
        try:
            initial_state: VRVAState = VRVAState(
                messages=[],
                db_path=self.db_path,
                files=self.files,
                competencia=competencia,
                current_step="Iniciando",
                processed_files={},
                calculations_done=False,
                report_generated=False,
                error=""
            )
            final_state = self.workflow.invoke(initial_state)

            if final_state.get("error"):
                logger.error("Erro no workflow: %s", final_state["error"])
                return False

            return final_state.get("report_generated", False)
        except Exception as e:
            logger.exception("Erro ao executar workflow")
            return False