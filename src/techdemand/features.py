"""Variáveis derivadas usadas em todas as análises."""
from __future__ import annotations

import pandas as pd

from . import config


def tech_employment(panel: pd.DataFrame) -> pd.Series:
    """Emprego no núcleo tech (milhares): soma das séries CES de computação."""
    s = panel[config.TECH_EMPLOYMENT_SERIES].dropna().sum(axis=1)
    s.name = "tech_emp"
    return s


def tech_share(panel: pd.DataFrame) -> pd.Series:
    """Participação do núcleo tech no emprego total não agrícola (%)."""
    s = (tech_employment(panel) / panel["PAYEMS"] * 100).dropna()
    s.name = "tech_share"
    return s


def rebase(s: pd.Series, base) -> pd.Series:
    """Reindexa a série para base = 100 na data (ou período) indicada."""
    return s / s.loc[base].mean() * 100


def yoy(s: pd.Series, periods: int = 12) -> pd.Series:
    """Variação percentual em relação ao mesmo período do ano anterior."""
    return s.pct_change(periods, fill_method=None) * 100


def annual(s: pd.Series, complete_only: bool = True) -> pd.Series:
    """Média anual; por padrão descarta o ano corrente incompleto."""
    counts = s.groupby(s.index.year).count()
    out = s.groupby(s.index.year).mean()
    if complete_only:
        out = out[counts >= 12]
    out.index.name = "year"
    return out


def recession_spans(usrec: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Intervalos (início, fim) de recessões a partir do indicador NBER 0/1."""
    flag = usrec.fillna(0).astype(int)
    starts = flag.index[(flag == 1) & (flag.shift(1, fill_value=0) == 0)]
    ends = flag.index[(flag == 1) & (flag.shift(-1, fill_value=0) == 0)]
    return list(zip(starts, ends))
