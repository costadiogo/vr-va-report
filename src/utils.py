import pandas as pd
import numpy as np
import unicodedata
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Tuple

# -----------------------
# Utilidades
# -----------------------
def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn')

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        strip_accents(str(c)).strip().lower().replace(" ", "_").replace("__", "_")
        for c in df.columns
    ]
    return df

def safe_date(x) -> Optional[date]:
    if pd.isna(x) or x is None or x == "":
        return None
    if isinstance(x, (datetime, date)):
        return x.date() if isinstance(x, datetime) else x
    try:
        return pd.to_datetime(x, dayfirst=True, errors="coerce").date()
    except Exception:
        return None

def month_bounds(year: int, month: int) -> Tuple[date, date]:
    first = date(year, month, 1)
    last = (first + relativedelta(day=31))
    return first, last

def busdays(start: date, end: date) -> int:
    if not start or not end or end < start:
        return 0
    # count inclusive of start..end business days
    return int(np.busday_count(start, (end + timedelta(days=1))))

def within_period(pstart, pend, start, end) -> Tuple[Optional[date], Optional[date]]:
    # Converte NaN para None
    if pd.isna(pstart):
        return None, None
    if pd.isna(pend):
        pend = end  # sem data de demissão = ativo até o fim do período

    # Garante que tudo é datetime.date
    if isinstance(pstart, pd.Timestamp):
        pstart = pstart.date()
    if isinstance(pend, pd.Timestamp):
        pend = pend.date()
    if isinstance(start, pd.Timestamp):
        start = start.date()
    if isinstance(end, pd.Timestamp):
        end = end.date()

    s = max(pstart, start) if start else pstart
    e = min(pend, end) if end else pend

    if e < s:
        return None, None
    return s, e