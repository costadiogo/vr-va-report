import pandas as pd
import sqlite3

from src.logger.logger import logger

def process_fired(db_path: str, df_dismisseds: pd.DataFrame):
    """Processa desligamentos com regra do dia 15 e aplica observações."""

    df_dismisseds['DATA DEMISSÃO'] = pd.to_datetime(
        df_dismisseds['DATA DEMISSÃO'], dayfirst=True, errors='coerce'
    )
    df_dismissed = df_dismisseds[['MATRICULA', 'DATA DEMISSÃO', 'COMUNICADO DE DESLIGAMENTO']].copy()
    df_dismissed.rename(columns={
        'DATA DEMISSÃO': 'DATA_DEMISSAO',
        'COMUNICADO DE DESLIGAMENTO': 'COMUNICADO_DESLIGAMENTO'
    }, inplace=True)
    df_dismissed['MATRICULA'] = df_dismissed['MATRICULA'].astype(str).str.strip()

    def payment(row):
        if pd.isna(row['DATA_DEMISSAO']):
            return 'Excluir', ''
        dia = row['DATA_DEMISSAO'].day
        if dia <= 15:
            if str(row.get('COMUNICADO_DESLIGAMENTO')).strip().upper() == 'OK':
                return 'Excluir', ''
            else:
                return 'Integral', ''
        else:
            return 'Proporcional', 'Desconto proporcional em rescisão'

    df_dismissed[['TIPO_PAGAMENTO', 'OBS_GERAL']] = df_dismissed.apply(
        lambda row: pd.Series(payment(row)), axis=1
    )

    df_dismissed_filter = df_dismissed[df_dismissed['TIPO_PAGAMENTO'] != 'Excluir']

    with sqlite3.connect(db_path) as conn:
        df_base = pd.read_sql('SELECT * FROM report', conn)
        df_base['MATRICULA'] = df_base['MATRICULA'].astype(str).str.strip()

        df_merge = df_base.merge(df_dismissed_filter, on="MATRICULA", how="left", suffixes=("", "_DEM"))

        for col in ["DATA_DEMISSAO", "COMUNICADO_DESLIGAMENTO", "TIPO_PAGAMENTO", "OBS_GERAL"]:
            if col + "_DEM" in df_merge.columns:
                df_merge[col] = df_merge[col].fillna(df_merge[col + "_DEM"])
                df_merge.drop(columns=[col + "_DEM"], inplace=True)
                
        df_merge = df_merge[df_merge['TIPO_PAGAMENTO'].isin(['Integral', 'Proporcional']) | df_merge['TIPO_PAGAMENTO'].isna()]

        df_merge.to_sql('report', conn, if_exists='replace', index=False)

    logger.info(f"✅ Processados {len(df_dismissed_filter)} desligamentos com regras do dia 15/16")