import pandas as pd
import sqlite3
from src.state_union import infer_state_from_union

from src.logger.logger import logger

def process_admissions(db_path: str, df_admissions: pd.DataFrame, df_actives: pd.DataFrame):
    """Processa admissões do mês, atualizando registros existentes e inserindo novos registros elegíveis."""

    df_adm = df_admissions[['MATRICULA', 'Admissão', 'Cargo']].copy()
    df_adm.rename(columns={'Admissão': 'ADMISSAO', 'Cargo': 'CARGO'}, inplace=True)
    df_adm['MATRICULA'] = df_adm['MATRICULA'].astype(str).str.strip()

    remove_positions = ["GERENTE", "ESTAGIARIO", "ESTAGIO", "APRENDIZ"]
    df_adm = df_adm[df_adm["CARGO"].apply(lambda c: not any(rc in c.upper() for rc in remove_positions))]

    if df_adm.empty:
        logger.info("⚠️ Nenhuma admissão elegível encontrada.")
        return

    df_adm['SITUACAO'] = "Admissão no mês"

    df_actives = df_actives[['MATRICULA', 'Sindicato']].copy()
    df_actives.rename(columns={'Sindicato': 'SINDICATO'}, inplace=True)
    df_actives['MATRICULA'] = df_actives['MATRICULA'].astype(str).str.strip()

    df_adm = df_adm.merge(df_actives, on="MATRICULA", how="left")

    df_adm['ESTADO'] = df_adm['SINDICATO'].apply(lambda s: infer_state_from_union(s) if pd.notna(s) else None)

    with sqlite3.connect(db_path) as conn:
        df_base = pd.read_sql('SELECT * FROM report', conn)
        df_base['MATRICULA'] = df_base['MATRICULA'].astype(str).str.strip()

        df_base = df_base.merge(
            df_adm[['MATRICULA', 'ADMISSAO']],
            on='MATRICULA',
            how='left',
            suffixes=('', '_ADM')
        )
        
        if 'ADMISSAO_ADM' in df_base.columns:
            df_base['ADMISSAO'] = df_base['ADMISSAO_ADM'].combine_first(df_base['ADMISSAO'])
            df_base.drop(columns=['ADMISSAO_ADM'], inplace=True)

        df_news = df_adm[~df_adm['MATRICULA'].isin(df_base['MATRICULA'])].copy()

        df_news = df_news[df_news['SINDICATO'].notna() & (df_news['SINDICATO'] != '')]
        
        if not df_news.empty:
            df_base = pd.concat([df_base, df_news], ignore_index=True)
            logger.info(f"✅ Adicionadas {len(df_news)} novas admissões ao report")

        df_base.to_sql('report', conn, if_exists='replace', index=False)
        logger.info(f"✅ Admitidos processados e registros existentes atualizados")
