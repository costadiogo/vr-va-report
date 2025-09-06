import pandas as pd
import sqlite3

from src.logger.logger import logger

def process_actives(db_path: str, df_actives: pd.DataFrame):
        """Processa funcionários ativos."""
        
        df_actives.columns = df_actives.columns.str.strip()
        
        df = df_actives[['MATRICULA', 'TITULO DO CARGO', 'DESC. SITUACAO', 'Sindicato']].copy()
        df.rename(columns={
            'DESC. SITUACAO': 'SITUACAO',
            'Sindicato': 'SINDICATO',
            'TITULO DO CARGO': 'CARGO'
            }, inplace=True)
        
        # Limpar dados
        df['MATRICULA'] = df['MATRICULA'].astype(str).str.strip()
        df['SITUACAO'] = df['SITUACAO'].astype(str).str.strip()
        df['SINDICATO'] = df['SINDICATO'].astype(str).str.strip()
        df['CARGO'] = df['CARGO'].astype(str).str.strip()
        
        exclusions = ["GERENTE", "APRENDIZ", "ESTAGIARIO", "DIRETOR"]

        df_filter = df[~df['CARGO'].str.upper().str.startswith(tuple(exclusions))]
        
        logger.info(f"✅ Processados {len(df_filter)} ativos")
        
        with sqlite3.connect(db_path) as conn:
            df_filter.to_sql('report', conn, if_exists='replace', index=False)