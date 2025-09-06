import pandas as pd
import sqlite3

from src.logger.logger import logger

def process_vacation(db_path: str, df_vacations: pd.DataFrame):
    """Aplica desconto de dias de férias no cálculo de dias úteis da base report."""

    df_vacations.rename(columns={'DIAS DE FÉRIAS': 'DIAS_DE_FERIAS'}, inplace=True)
    df_vacations['MATRICULA'] = df_vacations['MATRICULA'].astype(str).str.strip()
    df_vacations = df_vacations.groupby("MATRICULA", as_index=False)["DIAS_DE_FERIAS"].sum().reset_index()

    with sqlite3.connect(db_path) as conn:
        df_base = pd.read_sql('SELECT * FROM report', conn)
        df_base['MATRICULA'] = df_base['MATRICULA'].astype(str).str.strip()

        df_base = df_base.merge(
            df_vacations[['MATRICULA', 'DIAS_DE_FERIAS']],
            on='MATRICULA',
            how='left'
        )

        if 'DIAS_DE_FERIAS' not in df_base.columns:
            df_base['DIAS_DE_FERIAS'] = 0
        else:
            df_base['DIAS_DE_FERIAS'] = df_base['DIAS_DE_FERIAS'].fillna(0).astype(int)

        df_base['DIAS_UTEIS'] = (df_base['DIAS_UTEIS'] - df_base['DIAS_DE_FERIAS']).clip(lower=0)

        df_base.to_sql('report', conn, if_exists='replace', index=False)

    logger.info("✅ Ajuste de férias aplicado nos dias úteis")

    
    