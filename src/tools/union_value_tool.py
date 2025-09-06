import sqlite3
import pandas as pd

from src.logger.logger import logger

def process_daily_values(db_path: str):
    """Atualiza valores diários e inicializa campos de cálculo."""

    DAILY_VALUE_BY_STATE = {
        "Paraná": 35.0,
        "Rio de Janeiro": 35.0,
        "Rio Grande do Sul": 35.0,
        "São Paulo": 37.5
    }

    with sqlite3.connect(db_path) as conn:
        df_base = pd.read_sql('SELECT * FROM report', conn)
        df_base['VALOR_DIARIO'] = df_base['ESTADO'].map(DAILY_VALUE_BY_STATE).fillna(0.0)

        if 'TOTAL' not in df_base.columns:
            df_base['TOTAL'] = 0.0
        if 'CUSTO_EMPRESA' not in df_base.columns:
            df_base['CUSTO_EMPRESA'] = 0.0
        if 'CUSTO_PROFISSIONAL' not in df_base.columns:
            df_base['CUSTO_PROFISSIONAL'] = 0.0
        if 'OBS_GERAL' not in df_base.columns:
            df_base['OBS_GERAL'] = ""

        df_base.to_sql('report', conn, if_exists='replace', index=False)

    logger.info("✅ Valores diários aplicados por estado")
