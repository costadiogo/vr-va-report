import pandas as pd
import sqlite3

from src.logger.logger import logger

def process_vacation(db_path: str, df_vacation: pd.DataFrame):
    """Aplica desconto de dias de férias no cálculo de dias úteis da base report."""

    df_vacation.rename(columns={'DIAS DE FÉRIAS': 'DIAS_DE_FERIAS'}, inplace=True)
    df_vacation['MATRICULA'] = df_vacation['MATRICULA'].astype(str).str.strip()
    df_vacation = df_vacation.groupby("MATRICULA", as_index=False)["DIAS_DE_FERIAS"].sum().reset_index()

    with sqlite3.connect(db_path) as conn:
        df_base = pd.read_sql('SELECT * FROM report', conn)
        df_base['MATRICULA'] = df_base['MATRICULA'].astype(str).str.strip()

        if 'DIAS_DE_FERIAS' in df_base.columns:
            df_base = df_base.merge(
                df_vacation[['MATRICULA', 'DIAS_DE_FERIAS']],
                on='MATRICULA',
                how='left',
                suffixes=('', '_FERIAS')
            )
            df_base['DIAS_DE_FERIAS'] = df_base['DIAS_DE_FERIAS'].fillna(0) + df_base['DIAS_DE_FERIAS_FERIAS'].fillna(0)
            df_base.drop(columns=['DIAS_DE_FERIAS_FERIAS'], inplace=True)
        else:
            df_base = df_base.merge(
                df_vacation[['MATRICULA', 'DIAS_DE_FERIAS']],
                on='MATRICULA',
                how='left'
            )
            df_base['DIAS_DE_FERIAS'] = df_base['DIAS_DE_FERIAS'].fillna(0)

    df_base.to_sql('report', conn, if_exists='replace', index=False)

    
    