import pandas as pd
import sqlite3

from src.logger.logger import logger

def process_actives(db_path: str, df_actives: pd.DataFrame):
    """Processa funcionários ativos, excluindo aprendizes, estagiários, diretores,
        licença maternidade e auxílio doença.
    """
    
    df_actives.columns = df_actives.columns.str.strip()
    
    df = df_actives[['MATRICULA', 'TITULO DO CARGO', 'DESC. SITUACAO', 'Sindicato']].copy()
    df.rename(columns={
        'DESC. SITUACAO': 'SITUACAO',
        'Sindicato': 'SINDICATO',
        'TITULO DO CARGO': 'CARGO'
    }, inplace=True)
    
    df['MATRICULA'] = df['MATRICULA'].astype(str).str.strip()
    df['SITUACAO'] = df['SITUACAO'].astype(str).str.strip()
    df['SINDICATO'] = df['SINDICATO'].astype(str).str.strip()
    df['CARGO'] = df['CARGO'].astype(str).str.strip()

    exclusions = ["APRENDIZ", "ESTAGIARIO", "DIRETOR"]
    df = df[~df['CARGO'].str.upper().str.startswith(tuple(exclusions))]
    exclusions_situation = ["LICENÇA MATERNIDADE", "AUXÍLIO DOENÇA"]
    df = df[~df['SITUACAO'].str.upper().isin(exclusions_situation)]
    
    logger.info(f"✅ Processados {len(df)} ativos após exclusões")
    
    with sqlite3.connect(db_path) as conn:
        df.to_sql('report', conn, if_exists='replace', index=False)