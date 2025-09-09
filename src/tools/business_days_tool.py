import pandas as pd
import sqlite3
from src.state_union import infer_state_from_union

from src.logger.logger import logger

BUSINESS_DAYS_BY_STATE = {
    "São Paulo": 22,
    "Rio de Janeiro": 21,
    "Rio Grande do Sul": 21,
    "Paraná": 22
}

PERIOD_START = pd.to_datetime("2025-04-15")
PERIOD_END = pd.to_datetime("2025-05-15")

def business_days_between(start, end, holidays=None):
    """Conta days úteis entre start e end, excluindo feriados se fornecidos."""
    if pd.isna(start) or pd.isna(end) or end < start:
        return 0
    rng = pd.bdate_range(start=start, end=end, holidays=holidays)
    return len(rng)

def calculates_proportional_days(estado: str, admission, dismisseds, holidays_days: int, holidays_by_estado: dict = None):
    """
    Calcula dias úteis proporcionais entre periodo incial e preiodo final,
    considerando admissão, demissão, férias e feriados.
    """
    total_days = BUSINESS_DAYS_BY_STATE.get(estado, 0)
    if total_days == 0:
        return 0

    start = PERIOD_START if pd.isna(admission) else max(PERIOD_START, pd.to_datetime(admission))
    end = PERIOD_END if pd.isna(dismisseds) else min(PERIOD_END, pd.to_datetime(dismisseds))
    if start > end:
        return 0

    holidays = None
    if holidays_by_estado and estado in holidays_by_estado:
        holidays = holidays_by_estado[estado]

    total_bd_period = business_days_between(PERIOD_START, PERIOD_END, holidays=holidays)
    bd_between = business_days_between(start, end, holidays=holidays)

    if total_bd_period == 0:
        days_period = (end - start).days + 1
        total_period = (PERIOD_END - PERIOD_START).days + 1
        days = int(round(total_days * days_period / total_period))
    else:
        days = int(round(total_days * bd_between / total_bd_period))

    days -= int(holidays_days or 0)
    return max(0, days)


def process_business_days(db_path: str, holidays_by_estado: dict = None):
    """Atualiza coluna DIAS_UTEIS considerando admissões, demissões e férias."""
    with sqlite3.connect(db_path) as conn:
        df_base = pd.read_sql('SELECT * FROM report', conn)

        for col in ["ADMISSAO", "DATA_DEMISSAO"]:
            if col in df_base.columns:
                df_base[col] = pd.to_datetime(df_base[col], errors="coerce")

        if 'DIAS_DE_FERIAS' not in df_base.columns:
            df_base['DIAS_DE_FERIAS'] = 0
        else:
            df_base['DIAS_DE_FERIAS'] = df_base['DIAS_DE_FERIAS'].fillna(0).astype(int)

        df_base['ESTADO'] = df_base['SINDICATO'].apply(infer_state_from_union)

        df_base['DIAS_UTEIS'] = df_base.apply(
            lambda row: calculates_proportional_days(
                row['ESTADO'],
                row.get('ADMISSAO'),
                row.get('DATA_DEMISSAO'),
                row.get('DIAS_DE_FERIAS', 0),
                holidays_by_estado
            ),
            axis=1
        )

        df_base.to_sql('report', conn, if_exists='replace', index=False)

    logger.info("✅ Dias úteis proporcionais processados com sucesso")