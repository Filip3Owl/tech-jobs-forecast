"""Coleta de dados reais com cache local em data/raw.

Cada função baixa a fonte uma única vez e reaproveita o arquivo salvo, o que
torna as análises reproduzíveis e evita requisições repetidas.
"""
from __future__ import annotations

import json
import time
from itertools import product
from pathlib import Path

import pandas as pd
import requests

from . import config


def _download(url: str, dest: Path, refresh: bool = False, retries: int = 3) -> Path:
    if dest.exists() and not refresh:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, retries + 1):
        try:
            # User-Agent padrão do requests: o FRED retém conexões de UAs de navegador.
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            return dest
        except requests.RequestException:
            if attempt == retries:
                raise
            time.sleep(2 * attempt)
    return dest


def fetch_fred(series_id: str, refresh: bool = False) -> pd.Series:
    """Série mensal do FRED como pd.Series indexada por data."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    path = _download(url, config.DATA_RAW / f"fred_{series_id}.csv", refresh)
    df = pd.read_csv(path, parse_dates=["observation_date"], na_values=["."])
    s = df.set_index("observation_date")[series_id].astype(float).dropna()
    s.index.name = "date"
    s.name = series_id
    return s


def fetch_fred_panel(series_ids=None, refresh: bool = False) -> pd.DataFrame:
    """Várias séries do FRED alinhadas em frequência mensal (média do mês).

    As séries do Indeed são diárias e as do BLS mensais; a média mensal
    coloca todas na mesma base temporal sem descartar observações.
    """
    series_ids = series_ids or list(config.FRED_SERIES)
    panel = pd.concat([fetch_fred(s, refresh) for s in series_ids], axis=1)
    return panel.resample("MS").mean()


def fetch_indeed_sectors(country: str = "US", refresh: bool = False) -> pd.DataFrame:
    """Índice diário de vagas do Indeed por setor (fev/2020 = 100)."""
    fname = f"job_postings_by_sector_{country}.csv"
    url = f"{config.INDEED_BASE}/{country}/{fname}"
    path = _download(url, config.DATA_RAW / f"indeed_{fname}", refresh)
    df = pd.read_csv(path, parse_dates=["date"])
    return df.rename(columns={"indeed_job_postings_index": "index", "display_name": "sector"})


def fetch_indeed_all_countries(refresh: bool = False) -> pd.DataFrame:
    frames = []
    for c in config.INDEED_COUNTRIES:
        df = fetch_indeed_sectors(c, refresh)
        frames.append(df.assign(jobcountry=c))
    return pd.concat(frames, ignore_index=True)


def _parse_jsonstat(payload: dict) -> pd.DataFrame:
    """Converte um dataset JSON-stat 2.0 (formato do Eurostat) em formato longo."""
    dims = payload["id"]
    cats = []
    for d in dims:
        index = payload["dimension"][d]["category"]["index"]
        ordered = sorted(index, key=index.get) if isinstance(index, dict) else index
        cats.append(ordered)
    values = payload["value"]
    rows = []
    for flat, combo in enumerate(product(*cats)):
        v = values.get(str(flat)) if isinstance(values, dict) else values[flat]
        if v is not None:
            rows.append((*combo, v))
    return pd.DataFrame(rows, columns=[*dims, "value"])


def fetch_eurostat_ict(refresh: bool = False) -> pd.DataFrame:
    """Especialistas em TIC empregados por país/ano (THS_PER e PC_EMP)."""
    ds = config.EUROSTAT_ICT_DATASET
    url = (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
        f"{ds}?format=JSON&lang=EN"
    )
    path = _download(url, config.DATA_RAW / f"eurostat_{ds}.json", refresh)
    payload = json.loads(path.read_text())
    df = _parse_jsonstat(payload)
    df["time"] = df["time"].astype(int)
    labels = payload["dimension"]["geo"]["category"]["label"]
    df["geo_name"] = df["geo"].map(labels)
    return df.drop(columns="freq")


def load_bls_projections() -> pd.DataFrame:
    """Projeções oficiais BLS 2025–2035 para ocupações de computação e matemática."""
    return pd.read_csv(config.BLS_PROJECTIONS_FILE, dtype={"soc_code": str})

