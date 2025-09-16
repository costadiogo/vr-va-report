import pandas as pd
import sqlite3

from src.logger.logger import logger

def process_admissions(db_path: str, df_admissions: pd.DataFrame, df_actives: pd.DataFrame):
    """
    Processa admissões do mês:
      - Atualiza ADMISSAO em registros existentes no report.
      - Adiciona novas matrículas encontradas em admissions mas não presentes em report.
      - Para essas novas, se não houver SINDICATO no df_admissions/df_actives,
        herda o último SINDICATO disponível no report.
      - Infere ESTADO a partir do SINDICATO (usando a função disponível).
    """
    df_adm = df_admissions[['MATRICULA', 'Admissão', 'Cargo']].copy()
    df_adm.rename(columns={'Admissão': 'ADMISSAO', 'Cargo': 'CARGO'}, inplace=True)
    df_adm['MATRICULA'] = df_adm['MATRICULA'].astype(str).str.strip()

    remove_positions = ["DIRETOR", "ESTAGIARIO", "ESTAGIO", "APRENDIZ"]
    df_adm = df_adm[df_adm["CARGO"].apply(lambda c: not any(rc in c.upper() for rc in remove_positions))]

    if df_adm.empty:
        logger.info("⚠️ Nenhuma admissão elegível encontrada.")
        return

    df_adm['SITUACAO'] = "Admissão no mês"

    df_actives = df_actives[['MATRICULA', 'Sindicato']].copy()
    df_actives.rename(columns={'Sindicato': 'SINDICATO'}, inplace=True)
    df_actives['MATRICULA'] = df_actives['MATRICULA'].astype(str).str.strip()

    df_adm = df_adm.merge(df_actives, on='MATRICULA', how='left')

    if 'infer_state_from_union' in globals() and callable(globals()['infer_state_from_union']):
        infer_state_fn = globals()['infer_state_from_union']
    elif 'infer_estado_from_sindicato' in globals() and callable(globals()['infer_estado_from_sindicato']):
        infer_state_fn = globals()['infer_estado_from_sindicato']
    else:
        infer_state_fn = lambda s: None

    with sqlite3.connect(db_path) as conn:
        df_report = pd.read_sql('SELECT * FROM report', conn)
        
        if 'MATRICULA' not in df_report.columns:
            logger.error("Tabela report não contém coluna 'MATRICULA'. Abortando processamento de admissões.")
            return
        df_report['MATRICULA'] = df_report['MATRICULA'].astype(str).str.strip()

        if 'ADMISSAO' not in df_report.columns:
            df_report['ADMISSAO'] = pd.NaT

        df_report = df_report.merge(
            df_adm[['MATRICULA', 'ADMISSAO']],
            on='MATRICULA',
            how='left',
            suffixes=('', '_ADM')
        )
        if 'ADMISSAO_ADM' in df_report.columns:
            df_report['ADMISSAO'] = df_report['ADMISSAO_ADM'].combine_first(df_report['ADMISSAO'])
            df_report.drop(columns=['ADMISSAO_ADM'], inplace=True)

        df_news = df_adm[~df_adm['MATRICULA'].isin(df_report['MATRICULA'])].copy()

        if not df_news.empty:
            if 'SINDICATO' not in df_news.columns:
                df_news['SINDICATO'] = None

            last_union = None
            if 'SINDICATO' in df_report.columns and df_report['SINDICATO'].notna().any():
                last_union = df_report['SINDICATO'].dropna().iloc[-1]

            if last_union:
                df_news['SINDICATO'] = df_news['SINDICATO'].fillna(last_union)

            df_news['ESTADO'] = df_news['SINDICATO'].apply(lambda s: infer_state_fn(s) if pd.notna(s) and s != '' else None)

            df_news = df_news[df_news['SINDICATO'].notna() & (df_news['SINDICATO'] != '')]

            if not df_news.empty:
                df_report = pd.concat([df_report, df_news], ignore_index=True, sort=False)
                logger.info(f"✅ Adicionadas {len(df_news)} novas admissões ao report herdando sindicato do último registro")
            else:
                logger.info("⚠️ Havia novas matrículas, mas nenhuma com sindicato após tentativa de herdar. Nenhuma inserida.")
        else:
            logger.info("⚠️ Nenhuma matrícula divergente encontrada para inserir.")

        df_report.to_sql('report', conn, if_exists='replace', index=False)
        logger.info("✅ Admitidos processados e registros existentes atualizados")
