import pandas as pd
import numpy as np
from . import utils
from . import format_value
from . import state_union
from typing import Optional

# -----------------------
# Core Function
# -----------------------
def process_vr(
    active_xlsx: str,
    admitted_month_xlsx: Optional[str],
    fired_xlsx: Optional[str],
    vacation_xlsx: Optional[str],
    absence_xlsx: Optional[str],
    interns_xlsx: Optional[str],
    apprentice_xlsx: Optional[str],
    exterior_xlsx: Optional[str],
    working_days_basis_xlsx: Optional[str],
    union_base_values_xlsx: Optional[str]
) -> pd.DataFrame:

    print("=" * 50)
    print("INICIANDO PROCESSAMENTO VR/VA")
    print("=" * 50)

    # -----------------------
    # 1) Leitura e normalização
    # -----------------------
    print("\n1. LENDO ARQUIVOS...")
    
    # ATIVOS
    df_actives = pd.read_excel(active_xlsx)
    print(f"   Ativos: {len(df_actives)} registros")
    df_actives = utils.norm_cols(df_actives)

    # ADMITIDOS (abril, p.ex.)
    if admitted_month_xlsx:
        df_admitted = pd.read_excel(admitted_month_xlsx)
        df_admitted = utils.norm_cols(df_admitted)
        print(f"   Data admissao: {df_admitted}")
    else:
        df_admitted = pd.DataFrame()

    # DESLIGADOS
    if fired_xlsx:
        df_fired = pd.read_excel(fired_xlsx)
        df_fired = utils.norm_cols(df_fired)
        print(f"   Desligados: {len(df_fired)} registros")
    else:
        df_fired = pd.DataFrame()

    # FÉRIAS
    if vacation_xlsx:
        df_vacation = pd.read_excel(vacation_xlsx)
        df_vacation = utils.norm_cols(df_vacation)
        print(f"   Férias: {len(df_vacation)} registros")
    else:
        df_vacation = pd.DataFrame()

    # AFASTAMENTOS
    if absence_xlsx:
        df_absence = pd.read_excel(absence_xlsx)
        df_absence = utils.norm_cols(df_absence)
        print(f"   Afastamentos: {len(df_absence)} registros")
    else:
        df_absence = pd.DataFrame()

    # ESTAGIARIOS
    if interns_xlsx:
        df_interns = pd.read_excel(interns_xlsx)
        df_interns = utils.norm_cols(df_interns)
        print(f"   Estagiários: {len(df_interns)} registros")
    else:
        df_interns = pd.DataFrame()

    # APRENDIZES
    if apprentice_xlsx:
        df_apprentice = pd.read_excel(apprentice_xlsx)
        df_apprentice =utils. norm_cols(df_apprentice)
        print(f"   Aprendizes: {len(df_apprentice)} registros")
    else:
        df_apprentice = pd.DataFrame()

    # EXTERIOR
    if exterior_xlsx:
        df_exterior = pd.read_excel(exterior_xlsx)
        df_exterior = utils.norm_cols(df_exterior)
        print(f"   Exterior: {len(df_exterior)} registros")
        # Renomear "cadastro" para "matricula"
        if 'cadastro' in df_exterior.columns:
            df_exterior.rename(columns={'cadastro': 'matricula'}, inplace=True)
    else:
        df_exterior = pd.DataFrame()

    # DIAS ÚTEIS - CORREÇÃO: header na linha 1
    if working_days_basis_xlsx:
        df_working_days = pd.read_excel(working_days_basis_xlsx, header=1)
        df_working_days = utils.norm_cols(df_working_days)
        print(f"   Dias Úteis: {len(df_working_days)} registros")
        print(f"   Colunas Dias Úteis: {df_working_days.columns.tolist()}")
    else:
        df_working_days = pd.DataFrame()

    # SINDICATO x VALOR
    if union_base_values_xlsx:
        df_union_base_values = pd.read_excel(union_base_values_xlsx)
        print(f"   Colunas originais Sindicato x Valor: {df_union_base_values.columns.tolist()}")
        print(f"   Primeiras linhas Sindicato x Valor:")
        print(df_union_base_values.head())
        
        df_union_base_values = utils.norm_cols(df_union_base_values)
        print(f"   Colunas após normalização: {df_union_base_values.columns.tolist()}")
        
        # Limpar valores monetários
        def parse_val(v):
            if pd.isna(v): return np.nan
            s = str(v).replace("R$", "").strip()
            if "," in s:
                s = s.replace(".", "").replace(",", ".")
            try:
                return float(s)
            except (ValueError, TypeError):
                return np.nan

        if 'valor' in df_union_base_values.columns:
            # Use a nova função corrigida
            df_union_base_values['valor'] = df_union_base_values['valor'].map(parse_val)
            print(f"   Valores após limpeza: {df_union_base_values['valor'].tolist()}")
        else:
            df_union_base_values = pd.DataFrame()

    # -----------------------
    # 2) Consolidação e Tratamento de Exclusões
    # -----------------------
    print("\n2. CONSOLIDANDO E APLICANDO EXCLUSÕES...")
    
    # Base inicial: Ativos
    df_final = df_actives.copy()
    
    for df in [df_admitted, df_fired, df_vacation, df_absence, df_interns, df_apprentice, df_exterior, df_working_days, df_union_base_values]:
        if not df.empty and 'matricula' in df.columns:
            df['matricula'] = df['matricula'].astype(str).str.strip()
            
    if 'matricula' in df_final.columns:
        df_final['matricula'] = df_final['matricula'].astype(str).str.strip()
    
    # -------------------
    # EXCLUSÕES
    # -------------------

    # 1. Estagiários
    if not df_interns.empty:
        before = len(df_final)
        df_final = df_final[~df_final['matricula'].isin(df_interns['matricula'])]
        print(f"   Removidos estagiários: {before - len(df_final)}")
        
     # 2. Aprendizes
    if not df_apprentice.empty:
        before = len(df_final)
        df_final = df_final[~df_final['matricula'].isin(df_apprentice['matricula'])]
        print(f"   Removidos aprendizes: {before - len(df_final)}")

    # 3. Exterior
    if not df_exterior.empty:
        before = len(df_final)
        df_final = df_final[~df_final['matricula'].isin(df_exterior['matricula'])]
        print(f"   Removidos exterior: {before - len(df_final)}")

    # 4. Desligados
    if not df_fired.empty:
        before = len(df_final)
        df_final = df_final[~df_final['matricula'].isin(df_fired['matricula'])]
        print(f"   Removidos desligados: {before - len(df_final)}")
        
        if "data_demissao" in df_fired.columns:
            print("\n3. APLICANDO REGRAS DE DESLIGAMENTO...")
            
            # Normalizar datas
            df_fired["data_demissao"] = pd.to_datetime(df_fired["data_demissao"], errors="coerce")
            # Juntar desligados na base final (para olhar as datas e regras)
            df_final = df_final.merge(df_fired[["matricula", "data_demissao", "comunicado_de_desligamento"]], on="matricula", how="left")
            
            # Criar coluna auxiliar para marcar status
            df_final["status_desligamento"] = "ATIVO"
            
            # Regra 1: desligados até dia 15 com OK → remover
            mask_excluir = (
                df_final["data_demissao"].notna()
                & (df_final["data_demissao"].dt.day <= 15)
                & (df_final["comunicado_de_desligamento"].str.upper() == "OK")
            )
            excluidos = df_final.loc[mask_excluir, "matricula"].tolist()
            df_final = df_final[~mask_excluir]
            print(f"   Desligados até dia 15 com OK removidos: {len(excluidos)}")

            # Regra 2: desligados até dia 15 sem OK → VR integral
            mask_integral = (
                df_final["data_demissao"].notna()
                & (df_final["data_demissao"].dt.day <= 15)
                & (df_final["comunicado_de_desligamento"].isna() | (df_final["comunicado_de_desligamento"].str.upper() != "OK"))
            )
            df_final.loc[mask_integral, "status_desligamento"] = "VR INTEGRAL (sem OK até 15)"

            # Regra 3: desligados do dia 16 em diante → VR integral (ajuste só na rescisão)
            mask_integral_apos15 = (
                df_final["data_demissao"].notna()
                & (df_final["data_demissao"].dt.day > 15)
            )
            df_final.loc[mask_integral_apos15, "status_desligamento"] = "VR INTEGRAL (desligamento após 15)"

            print("   Regra de desligamentos aplicada.")

    # 5. Afastamentos (licenças em geral)
    if not df_absence.empty:
        before = len(df_final)
        df_final = df_final[~df_final['matricula'].isin(df_absence['matricula'])]
        print(f"   Removidos afastados: {before - len(df_final)}")

    # -------------------
    # Exclusão por Cargos (Diretor, Estagiário, Aprendiz)
    # -------------------
    if 'cargo' in df_final.columns:
        excluir_cargos = ["DIRETOR", "ESTAGIÁRIO", "APRENDIZ"]
        before = len(df_final)
        df_final = df_final[~df_final['cargo'].str.upper().isin(excluir_cargos)]
        print(f"   Removidos por cargo: {before - len(df_final)}")
        
    # 6. Férias
    if not df_vacation.empty:
        before = len(df_final)
        df_final = df_final[~df_final['matricula'].isin(df_vacation['matricula'])]
        print(f"   Removidos em férias: {before - len(df_final)}")

    print(f"   Base final após exclusões: {len(df_final)} registros")
    
    # -------------------
    # Relatório final
    # -------------------
    df_working_days.rename(columns={"sindicado": "sindicato", "dias_uteis": "Dias"}, inplace=True)
    df_union_base_values.rename(columns={"valor": "Valor"}, inplace=True)
    df_admitted["admissao"] = pd.to_datetime(df_admitted["admissao"], errors="coerce")
    df_admitted["matricula"] = df_admitted["matricula"].astype(str).str.strip()

    df_report = df_final[["matricula", "sindicato"]].copy()
    df_report["matricula"] = df_report["matricula"].astype(str).str.strip()
    df_report = df_report.merge(df_admitted[["matricula", "admissao"]], on="matricula", how="left")
    df_report["Competência"] = "05/2025"
    
    df_report["estado"] = df_report["sindicato"].apply(state_union.infer_estado_from_sindicato)
    df_report = df_report.merge(df_union_base_values, on="estado", how="left")
    
    df_report = df_report.merge(df_working_days[["sindicato", "Dias"]], on="sindicato", how="left")
    df_report["TOTAL"] = df_report["Valor"] * df_report["Dias"]
    df_report["Custo empresa"] = df_report["TOTAL"] * 0.8
    df_report["Desconto profissional"] = df_report["TOTAL"] * 0.2
    df_report["OBS GERAL"] = ""
    
    df_report["TOTAL"] = df_report["TOTAL"].apply(format_value.format_brl)
    df_report["Custo empresa"] = df_report["Custo empresa"].apply(format_value.format_brl)
    df_report["Desconto profissional"] = df_report["Desconto profissional"].apply(format_value.format_brl)
    
    df_report.rename(columns={"matricula": "Matricula"}, inplace=True)
    df_report.rename(columns={"sindicato": "Sindicato do Colaborador"}, inplace=True)
    df_report.rename(columns={"admissao": "Admissão"}, inplace=True)
    
    columns_report = [
        "Matricula",
        "Admissão",
        "Sindicato do Colaborador",
        "Competência",
        "Dias",
        "Valor",
        "TOTAL",
        "Custo empresa",
        "Desconto profissional",
        "OBS GERAL"
    ]

    report = df_report[columns_report].copy()
    return report