import pandas as pd
import sqlite3

from src.logger.logger import logger

STAR_PERIOD = pd.to_datetime("2025-04-15")
END_PERIOD = pd.to_datetime("2025-05-15")

def business_days_between(start, end):
    if pd.isna(start) or pd.isna(end) or end < start:
        return 0
    return len(pd.bdate_range(start, end))

def process_vacation(db_path: str, df_vacation: pd.DataFrame):
    """
    Atualiza dias úteis subtraindo os dias de férias que caem no período 15/04/2025 - 15/05/2025.
    """
    df_v = df_vacation.copy()
    df_v.rename(columns=lambda c: c.strip().upper().replace(" ", "_"), inplace=True)
    df_v["MATRICULA"] = df_v["MATRICULA"].astype(str).str.strip()

    if "DIAS_DE_FÉRIAS" in df_v.columns:
        df_v["DIAS_DE_FÉRIAS"] = pd.to_numeric(df_v["DIAS_DE_FÉRIAS"], errors="coerce").fillna(0).astype(int)

    if "DT_INICIO" in df_v.columns:
        df_v["DT_INICIO"] = pd.to_datetime(df_v["DT_INICIO"], errors="coerce")
    if "DT_FIM" in df_v.columns:
        df_v["DT_FIM"] = pd.to_datetime(df_v["DT_FIM"], errors="coerce")

    def calc_holidays_on_period(row):
        if "DT_INICIO" in row and "DT_FIM" in row and pd.notna(row["DT_INICIO"]) and pd.notna(row["DT_FIM"]):
            start = max(STAR_PERIOD, row["DT_INICIO"])
            end = min(END_PERIOD, row["DT_FIM"])
            return business_days_between(start, end) if end >= start else 0
        elif "DIAS_DE_FÉRIAS" in row:
            max_bd = business_days_between(STAR_PERIOD, END_PERIOD)
            return min(int(row["DIAS_DE_FÉRIAS"] or 0), max_bd)
        return 0

    df_v["FERIAS_NO_PERIODO"] = df_v.apply(calc_holidays_on_period, axis=1)
    df_v_agg = df_v.groupby("MATRICULA", as_index=False)["FERIAS_NO_PERIODO"].sum()

    with sqlite3.connect(db_path) as conn:
        df_report = pd.read_sql("SELECT * FROM report", conn)
        df_report["MATRICULA"] = df_report["MATRICULA"].astype(str).str.strip()

        df_merge = df_report.merge(df_v_agg, on="MATRICULA", how="left")
        df_merge["FERIAS_NO_PERIODO"] = df_merge["FERIAS_NO_PERIODO"].fillna(0).astype(int)

        df_merge["DIAS_UTEIS"] = pd.to_numeric(df_merge["DIAS_UTEIS"], errors="coerce").fillna(0).astype(int)
        df_merge["DIAS_UTEIS"] = (
            df_merge["DIAS_UTEIS"] - df_merge["FERIAS_NO_PERIODO"]
        )
        
        df_merge = df_merge[df_merge["DIAS_UTEIS"] > 0].copy()

        df_merge.drop(columns=["FERIAS_NO_PERIODO"], inplace=True)
        df_merge.to_sql("report", conn, if_exists="replace", index=False)
    logger.info(f"✅ Processados {len(df_v)} registros com dias de férias!")    
    