"""Técnicas de mineração de dados para séries temporais de emprego e vagas."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import ruptures as rpt
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import grangercausalitytests


def stl_log(s: pd.Series, period: int = 12) -> pd.DataFrame:
    """Decomposição STL robusta em log: tendência, sazonalidade e resíduo."""
    res = STL(np.log(s.dropna()), period=period, robust=True).fit()
    out = pd.DataFrame({"observed": res.observed, "trend": res.trend,
                        "seasonal": res.seasonal, "resid": res.resid})
    # Crescimento anualizado da tendência (% a.a.)
    out["trend_growth"] = (np.exp(out["trend"].diff(period)) - 1) * 100
    return out


def change_points(s: pd.Series, penalty: float = 10.0, min_size: int = 24) -> list[pd.Timestamp]:
    """Pontos de mudança de regime na média da série (PELT, custo L2)."""
    clean = s.dropna()
    signal = clean.to_numpy().reshape(-1, 1)
    algo = rpt.Pelt(model="l2", min_size=min_size).fit(signal)
    bkps = algo.predict(pen=penalty * np.var(signal))
    return [clean.index[b] for b in bkps[:-1]]


def regimes(s: pd.Series, breaks: list[pd.Timestamp]) -> pd.DataFrame:
    """Resumo de cada regime delimitado pelos pontos de mudança."""
    clean = s.dropna()
    edges = [clean.index[0], *breaks, clean.index[-1] + pd.Timedelta(days=1)]
    rows = []
    for a, b in zip(edges[:-1], edges[1:]):
        seg = clean[(clean.index >= a) & (clean.index < b)]
        rows.append({"início": seg.index[0], "fim": seg.index[-1],
                     "meses": len(seg), "média": seg.mean(), "desvio": seg.std()})
    return pd.DataFrame(rows)


@dataclass
class Drawdown:
    peak: pd.Timestamp
    trough: pd.Timestamp
    recovery: pd.Timestamp | None
    depth_pct: float
    months_to_trough: int
    months_to_recover: int | None


def drawdowns(s: pd.Series, min_depth_pct: float = 2.0) -> list[Drawdown]:
    """Episódios pico → vale → recuperação do pico anterior."""
    s = s.dropna()
    out, peak_date, peak_val = [], s.index[0], s.iloc[0]
    in_dd, trough_date, trough_val = False, None, None
    for d, v in s.items():
        if v >= peak_val:
            if in_dd:
                depth = (trough_val / peak_val - 1) * 100
                if -depth >= min_depth_pct:
                    out.append(_mk_dd(s, peak_date, trough_date, d, depth))
            in_dd, peak_date, peak_val = False, d, v
        else:
            if not in_dd or v < trough_val:
                trough_date, trough_val = d, v
            in_dd = True
    if in_dd:
        depth = (trough_val / peak_val - 1) * 100
        if -depth >= min_depth_pct:
            out.append(_mk_dd(s, peak_date, trough_date, None, depth))
    return out


def _months(a: pd.Timestamp, b: pd.Timestamp) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def _mk_dd(s, peak, trough, recovery, depth) -> Drawdown:
    return Drawdown(peak, trough, recovery, depth, _months(peak, trough),
                    _months(peak, recovery) if recovery is not None else None)


def mann_kendall(y: pd.Series) -> dict:
    """Teste de tendência monotônica de Mann-Kendall + inclinação de Theil-Sen."""
    y = y.dropna()
    x = np.asarray(y.index, dtype=float)
    tau, p = stats.kendalltau(x, y.to_numpy())
    slope, intercept, lo, hi = stats.theilslopes(y.to_numpy(), x)
    return {"tau": tau, "p_value": p, "slope": slope, "slope_lo": lo, "slope_hi": hi, "n": len(y)}


def lead_lag_corr(leader: pd.Series, follower: pd.Series, max_lag: int = 24) -> pd.Series:
    """Correlação de Pearson entre leader(t - lag) e follower(t) para cada defasagem."""
    df = pd.concat([leader, follower], axis=1, keys=["x", "y"]).dropna()
    return pd.Series({lag: df["y"].corr(df["x"].shift(lag)) for lag in range(max_lag + 1)},
                     name="corr").rename_axis("lag")


def granger_pvalues(cause: pd.Series, effect: pd.Series, max_lag: int = 12) -> pd.Series:
    """p-valores (teste F) de 'cause' Granger-causa 'effect', por defasagem."""
    df = pd.concat([effect, cause], axis=1).dropna()
    res = grangercausalitytests(df.to_numpy(), maxlag=max_lag)
    return pd.Series({lag: r[0]["ssr_ftest"][1] for lag, r in res.items()}, name="p_value")


def cluster_trajectories(wide: pd.DataFrame, k_range=range(2, 8), seed: int = 42) -> dict:
    """K-Means em trajetórias (colunas = entidades), com k escolhido por silhueta.

    Cada trajetória é usada em log, preservando nível e forma do ciclo.
    Retorna rótulos, silhuetas por k e coordenadas PCA 2D para visualização.
    """
    X = np.log(wide.T.dropna(axis=1).clip(lower=1e-3))
    sil = {}
    for k in k_range:
        labels = KMeans(n_clusters=k, n_init=20, random_state=seed).fit_predict(X)
        sil[k] = silhouette_score(X, labels)
    best_k = max(sil, key=sil.get)
    km = KMeans(n_clusters=best_k, n_init=20, random_state=seed).fit(X)
    pca = PCA(n_components=2, random_state=seed).fit(X)
    coords = pd.DataFrame(pca.transform(X), index=X.index, columns=["pc1", "pc2"])
    return {"labels": pd.Series(km.labels_, index=X.index, name="cluster"),
            "silhouette": pd.Series(sil, name="silhouette"),
            "k": best_k, "coords": coords,
            "explained": pca.explained_variance_ratio_}
