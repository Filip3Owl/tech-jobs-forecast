"""Modelos de previsão, backtesting com origem móvel e simulação Monte Carlo.

Todos os modelos trabalham com séries anuais em log e devolvem previsões no
nível original, indexadas pelos anos à frente.
"""
from __future__ import annotations

import itertools
import warnings
from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

Forecaster = Callable[[pd.Series, int], pd.Series]


def _future_index(y: pd.Series, h: int) -> pd.Index:
    return pd.Index(range(y.index[-1] + 1, y.index[-1] + h + 1), name=y.index.name)


def naive(y: pd.Series, h: int) -> pd.Series:
    """Referência: o futuro repete o último valor (crescimento zero)."""
    return pd.Series(y.iloc[-1], index=_future_index(y, h))


def theil_sen_trend(y: pd.Series, h: int, window: int | None = 15) -> pd.Series:
    """Tendência log-linear robusta (Theil-Sen) nos últimos `window` anos."""
    ly = np.log(y if window is None else y.iloc[-window:])
    slope, _, _, _ = stats.theilslopes(ly.to_numpy(), ly.index.to_numpy(dtype=float))
    steps = np.arange(1, h + 1)
    return pd.Series(np.exp(np.log(y.iloc[-1]) + slope * steps), index=_future_index(y, h))


def ets_damped(y: pd.Series, h: int) -> pd.Series:
    """Holt com tendência amortecida (ETS A,Ad,N) em log."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = ExponentialSmoothing(np.log(y.to_numpy()), trend="add", damped_trend=True).fit()
    return pd.Series(np.exp(fit.forecast(h)), index=_future_index(y, h))


def arima_auto(y: pd.Series, h: int, max_p: int = 2, max_q: int = 2) -> pd.Series:
    """ARIMA(p,1,q) com drift; ordem escolhida por AIC."""
    ly = np.log(y.to_numpy())
    best, best_aic = None, np.inf
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for p, q in itertools.product(range(max_p + 1), range(max_q + 1)):
            try:
                fit = ARIMA(ly, order=(p, 1, q), trend="t").fit()
            except (ValueError, np.linalg.LinAlgError):
                continue
            if fit.aic < best_aic:
                best, best_aic = fit, fit.aic
    return pd.Series(np.exp(best.forecast(h)), index=_future_index(y, h))


MODELS: dict[str, Forecaster] = {
    "Ingênuo (sem crescimento)": naive,
    "Tendência robusta (Theil-Sen 15a)": theil_sen_trend,
    "ETS amortecido": ets_damped,
    "ARIMA com drift": arima_auto,
}


def backtest(y: pd.Series, models: dict[str, Forecaster], origins, h: int = 10,
             min_train: int = 8) -> pd.DataFrame:
    """Avaliação fora da amostra com origem móvel (expanding window).

    Para cada ano de origem, treina com dados até a origem e compara as
    previsões com o realizado nos anos seguintes disponíveis.
    """
    rows = []
    for origin in origins:
        train = y.loc[:origin]
        if len(train) < min_train:
            continue
        actual = y.loc[origin + 1: origin + h]
        if actual.empty:
            continue
        for name, fn in models.items():
            fc = fn(train, h).reindex(actual.index)
            for year, a in actual.items():
                f = fc.loc[year]
                rows.append({"modelo": name, "origem": origin, "h": year - origin, "ano": year,
                             "previsto": f, "realizado": a,
                             "erro_pct": (f / a - 1) * 100})
    out = pd.DataFrame(rows)
    out["ape"] = out["erro_pct"].abs()
    return out


def skill_weights(bt: pd.DataFrame, horizons=range(5, 11), exclude=("Ingênuo (sem crescimento)",)) -> pd.Series:
    """Pesos do ensemble ∝ 1 / MAPE nos horizontes longos."""
    mape = bt[bt["h"].isin(list(horizons)) & ~bt["modelo"].isin(exclude)].groupby("modelo")["ape"].mean()
    w = 1 / mape
    return (w / w.sum()).rename("peso")


def ensemble(forecasts: dict[str, pd.Series], weights: pd.Series) -> pd.Series:
    """Média geométrica ponderada das previsões (equivale a média em log)."""
    logs = pd.DataFrame({k: np.log(v) for k, v in forecasts.items() if k in weights.index})
    return np.exp(logs.mul(weights[logs.columns], axis=1).sum(axis=1)).rename("Ensemble")


def block_bootstrap_paths(y: pd.Series, h: int, n_sims: int = 20_000, block: int = 3,
                          since: int | None = None, seed: int = 42) -> pd.DataFrame:
    """Caminhos simulados reamostrando blocos de crescimentos anuais históricos.

    Blocos consecutivos preservam a autocorrelação dos ciclos (anos ruins
    tendem a vir em sequência). Retorna um DataFrame (simulações × anos).
    """
    g = np.log(y).diff().dropna()
    if since is not None:
        g = g.loc[since:]
    g = g.to_numpy()
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(h / block))
    starts = rng.integers(0, len(g) - block + 1, size=(n_sims, n_blocks))
    sims = np.concatenate([g[starts + k][:, :, None] for k in range(block)], axis=2)
    sims = sims.reshape(n_sims, -1)[:, :h]
    paths = y.iloc[-1] * np.exp(np.cumsum(sims, axis=1))
    return pd.DataFrame(paths, columns=_future_index(y, h))


def equal_weight_ensemble(y: pd.Series, h: int) -> pd.Series:
    """Ensemble de pesos iguais dos três modelos de tendência (para o backtest)."""
    names = [k for k in MODELS if not k.startswith("Ingênuo")]
    return ensemble({k: MODELS[k](y, h) for k in names}, pd.Series(1 / len(names), index=names))


def empirical_interval(fc: pd.Series, bt_model: pd.DataFrame, lower: float = 0.1,
                       upper: float = 0.9) -> pd.DataFrame:
    """Intervalo de previsão a partir dos erros fora da amostra do backtest.

    Com erro e = previsto/realizado − 1, o realizado é previsto/(1 + e); os
    quantis de e em cada horizonte h viram as bandas do intervalo.
    """
    q = bt_model.groupby("h")["erro_pct"].quantile([lower, upper]).unstack() / 100
    h = np.arange(1, len(fc) + 1)
    q = q.reindex(h).ffill()
    return pd.DataFrame({"previsto": fc.to_numpy(),
                         "inferior": fc.to_numpy() / (1 + q[upper].to_numpy()),
                         "superior": fc.to_numpy() / (1 + q[lower].to_numpy())}, index=fc.index)


def structural_share(tech: pd.Series, total: pd.Series, h: int, total_growth_h: float,
                     window: int = 15) -> pd.DataFrame:
    """Modelo estrutural: participação do tech (tendência Theil-Sen) × emprego total projetado.

    `total_growth_h` é o crescimento acumulado do emprego total no horizonte
    (ex.: 0.035 para a projeção oficial do BLS de +3,5% em 10 anos).
    """
    share = (tech / total).dropna()
    recent = share.iloc[-window:]
    slope, _, _, _ = stats.theilslopes(recent.to_numpy(), recent.index.to_numpy(dtype=float))
    idx = _future_index(share, h)
    steps = np.arange(1, h + 1)
    share_fc = share.iloc[-1] + slope * steps
    total_fc = total.loc[share.index[-1]] * (1 + total_growth_h) ** (steps / h)
    return pd.DataFrame({"participacao": share_fc, "total": total_fc,
                         "tech": share_fc * total_fc}, index=idx)
