import numpy as np
import pandas as pd
import pytest

from techdemand import analysis


@pytest.fixture
def idx():
    return pd.date_range("2000-01-01", periods=120, freq="MS")


def test_drawdowns_detects_episode_and_recovery(idx):
    v = np.r_[np.linspace(100, 120, 30), np.linspace(120, 90, 20), np.linspace(90, 130, 70)]
    eps = analysis.drawdowns(pd.Series(v, index=idx))
    assert len(eps) == 1
    ep = eps[0]
    assert ep.depth_pct == pytest.approx(-25.0, abs=0.01)
    assert ep.months_to_trough == 19
    assert ep.recovery is not None and ep.months_to_recover > ep.months_to_trough


def test_drawdowns_open_episode(idx):
    v = np.r_[np.linspace(100, 120, 100), np.linspace(119, 110, 20)]
    ep = analysis.drawdowns(pd.Series(v, index=idx))[-1]
    assert ep.recovery is None and ep.months_to_recover is None


def test_change_points_finds_level_shift(idx):
    rng = np.random.default_rng(0)
    v = np.r_[np.full(60, 5.0), np.full(60, -1.0)] + rng.normal(0, 0.3, 120)
    bkps = analysis.change_points(pd.Series(v, index=idx), penalty=3)
    assert len(bkps) == 1
    assert abs((bkps[0] - idx[60]).days) < 100


def test_mann_kendall_increasing():
    y = pd.Series(np.arange(15) * 0.2 + np.random.default_rng(1).normal(0, 0.1, 15),
                  index=range(2010, 2025))
    r = analysis.mann_kendall(y)
    assert r["p_value"] < 0.01 and r["slope"] == pytest.approx(0.2, abs=0.05)


def test_lead_lag_recovers_known_lag(idx):
    rng = np.random.default_rng(2)
    x = pd.Series(rng.normal(size=120), index=idx).rolling(3).mean()
    y = x.shift(6)
    assert analysis.lead_lag_corr(x, y, 12).idxmax() == 6


def test_cluster_trajectories_separates_groups(idx):
    up = {f"up{i}": np.linspace(100, 200, 120) * (1 + 0.01 * i) for i in range(5)}
    down = {f"down{i}": np.linspace(100, 50, 120) * (1 + 0.01 * i) for i in range(5)}
    res = analysis.cluster_trajectories(pd.DataFrame({**up, **down}, index=idx), k_range=range(2, 4))
    assert res["k"] == 2
    labels = res["labels"]
    assert labels[[c for c in labels.index if c.startswith("up")]].nunique() == 1
    assert labels["up0"] != labels["down0"]
