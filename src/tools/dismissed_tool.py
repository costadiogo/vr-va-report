import pandas as pd
import sqlite3

from src.logger.logger import logger

def process_fired(db_path: str, df_dismisseds: pd.DataFrame):
    """
    Processa desligamentos:
      - Remove desligados até dia 15 com comunicado OK;
      - Mantém/adiciona desligados até dia 15 sem comunicado (Integral);
      - Ignora desligados após dia 16 (Proporcional, tratado em rescisão);
      - Novos desligados válidos recebem sindicato do último registro.
    """
    
    df_dis = df_dismisseds.copy()
    df_dis.rename(columns={
        'DATA DEMISSÃO': 'DATA_DEMISSAO',
        'COMUNICADO DE DESLIGAMENTO': 'COMUNICADO_DESLIGAMENTO'
    }, inplace=True)
    df_dis['DATA_DEMISSAO'] = pd.to_datetime(df_dis['DATA_DEMISSAO'], dayfirst=True, errors='coerce')
    df_dis['MATRICULA'] = df_dis['MATRICULA'].astype(str).str.strip()

    def payment(row):
        if pd.isna(row['DATA_DEMISSAO']):
            return 'Ignorar', ''
        day = row['DATA_DEMISSAO'].day
        if day <= 15:
            if str(row.get('COMUNICADO_DESLIGAMENTO')).strip().upper() == 'OK':
                return 'Excluir', ''
            else:
                return 'Integral', ''
        else:
            return 'Proporcional', 'Desconto proporcional em rescisão'

    df_dis[['TIPO_PAGAMENTO', 'OBS_GERAL']] = df_dis.apply(lambda r: pd.Series(payment(r)), axis=1)

    df_valid = df_dis[df_dis['TIPO_PAGAMENTO'] == 'Integral'].copy()

    with sqlite3.connect(db_path) as conn:
        df_base = pd.read_sql('SELECT * FROM report', conn)
        df_base['MATRICULA'] = df_base['MATRICULA'].astype(str).str.strip()

        df_merge = df_base.merge(df_valid, on="MATRICULA", how="left", suffixes=("", "_DIS"))
        for col in ["DATA_DEMISSAO", "COMUNICADO_DESLIGAMENTO", "TIPO_PAGAMENTO", "OBS_GERAL"]:
            if col + "_DIS" in df_merge.columns:
                df_merge[col] = df_merge[col].combine_first(df_merge[col + "_DIS"])
                df_merge.drop(columns=[col + "_DIS"], inplace=True)

        df_news = df_valid[~df_valid['MATRICULA'].isin(df_base['MATRICULA'])].copy()

        if not df_news.empty:
            last_union = df_base['SINDICATO'].iloc[-1] if 'SINDICATO' in df_base.columns else None
            df_news['SINDICATO'] = last_union
            df_merge = pd.concat([df_merge, df_news], ignore_index=True)
            
        df_merge.to_sql('report', conn, if_exists='replace', index=False)
        logger.info(f"✅ Desligamentos processados: {len(df_valid)} registros Integral adicionados")