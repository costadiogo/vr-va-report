import pandas as pd
import sqlite3

from src.logger.logger import logger

def process_fired(db_path: str, df_demisseds: pd.DataFrame):
    """Processa desligamentos com regra do dia 15 e aplica observações."""

    df_demisseds['DATA DEMISSÃO'] = pd.to_datetime(
        df_demisseds['DATA DEMISSÃO'], dayfirst=True, errors='coerce'
    )
    df_demissed = df_demisseds[['MATRICULA', 'DATA DEMISSÃO', 'COMUNICADO DE DESLIGAMENTO']].copy()
    df_demissed.rename(columns={
        'DATA DEMISSÃO': 'DATA_DEMISSAO',
        'COMUNICADO DE DESLIGAMENTO': 'COMUNICADO_DESLIGAMENTO'
    }, inplace=True)
    df_demissed['MATRICULA'] = df_demissed['MATRICULA'].astype(str).str.strip()

    def payment(row):
        if pd.isna(row['DATA_DEMISSAO']):
            return 'Excluir', ''

        dia = row['DATA_DEMISSAO'].day
        if dia <= 15:
            if row.get('COMUNICADO_DESLIGAMENTO') == 'OK':
                return 'Excluir', ''
            else:
                return 'Integral', ''
        else:
            return 'Integral', 'Desconto proporcional em rescisão'

    df_demissed[['TIPO_PAGAMENTO', 'OBS_GERAL']] = df_demissed.apply(
        lambda row: pd.Series(payment(row)), axis=1
    )

    df_demissed_filtrado = df_demissed[df_demissed['TIPO_PAGAMENTO'] != 'Excluir']

    with sqlite3.connect(db_path) as conn:
        df_base = pd.read_sql('SELECT * FROM report', conn)
        df_base['MATRICULA'] = df_base['MATRICULA'].astype(str).str.strip()

        df_merge = df_base.merge(df_demissed_filtrado, on="MATRICULA", how="left", suffixes=("", "_DEM"))

        for col in ["DATA_DEMISSAO", "COMUNICADO_DESLIGAMENTO", "TIPO_PAGAMENTO", "OBS_GERAL"]:
            if col + "_DEM" in df_merge.columns:
                df_merge[col] = df_merge[col].fillna(df_merge[col + "_DEM"])
                df_merge.drop(columns=[col + "_DEM"], inplace=True)

        df_merge.to_sql('report', conn, if_exists='replace', index=False)

    logger.info(f"✅ Processados {len(df_demissed_filtrado)} desligamentos com regras do dia 15/16")
