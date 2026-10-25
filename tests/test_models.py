import numpy as np
import pandas as pd
import pytest

from techdemand import models


@pytest.fixture
def growing():
    years = range(1990, 2021)
    rng = np.random.default_rng(0)
    return pd.Series(100 * np.exp(0.03 * np.arange(31) + rng.normal(0, 0.005, 31)), index=years)


@pytest.mark.parametrize("name", list(models.MODELS))
def test_models_return_h_future_years(growing, name):
    fc = models.MODELS[name](growing, 5)
    assert list(fc.index) == [2021, 2022, 2023, 2024, 2025]
    assert (fc > 0).all()


def test_trend_models_capture_growth(growing):
    for fn in (models.theil_sen_trend, models.arima_auto):
        implied = np.log(fn(growing, 10).iloc[-1] / growing.iloc[-1]) / 10
        assert implied == pytest.approx(0.03, abs=0.006)


def test_backtest_shapes_and_naive_error(growing):
    bt = models.backtest(growing, {"Ingênuo (sem crescimento)": models.naive}, origins=[2010, 2015], h=5)
    assert set(bt["h"]) == {1, 2, 3, 4, 5}
    # Série crescente: o ingênuo sempre subestima
    assert (bt["erro_pct"] < 0).all()


def test_skill_weights_sum_to_one(growing):
    bt = models.backtest(growing, models.MODELS, origins=[2005, 2008], h=10)
    w = models.skill_weights(bt)
    assert w.sum() == pytest.approx(1.0)
    assert "Ingênuo (sem crescimento)" not in w.index


def test_bootstrap_paths(growing):
    paths = models.block_bootstrap_paths(growing, h=10, n_sims=2000)
    assert paths.shape == (2000, 10)
    med_growth = np.log(paths.iloc[:, -1].median() / growing.iloc[-1]) / 10
    assert med_growth == pytest.approx(0.03, abs=0.005)


def test_empirical_interval_brackets_forecast():
    fc = pd.Series([100.0, 110.0], index=[2026, 2027])
    bt = pd.DataFrame({"h": [1, 1, 1, 2, 2, 2], "erro_pct": [-10, 0, 10, -20, 0, 20]})
    iv = models.empirical_interval(fc, bt)
    assert (iv["inferior"] < iv["previsto"]).all() and (iv["superior"] > iv["previsto"]).all()
    assert iv.loc[2027, "superior"] - iv.loc[2027, "inferior"] > iv.loc[2026, "superior"] - iv.loc[2026, "inferior"]


def test_structural_share_constant_share():
    years = range(2000, 2021)
    total = pd.Series(1000.0, index=years)
    tech = pd.Series(20.0, index=years)
    out = models.structural_share(tech, total, h=10, total_growth_h=0.10)
    assert out["participacao"].iloc[-1] == pytest.approx(0.02)
    assert out["tech"].iloc[-1] == pytest.approx(22.0)
