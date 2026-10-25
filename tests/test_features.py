import pandas as pd
import pytest

from techdemand import features


@pytest.fixture
def monthly():
    idx = pd.date_range("2020-01-01", periods=30, freq="MS")
    return pd.Series(range(100, 130), index=idx, dtype=float)


def test_annual_drops_incomplete_year(monthly):
    out = features.annual(monthly)
    assert list(out.index) == [2020, 2021]
    assert out.loc[2020] == pytest.approx(105.5)


def test_rebase(monthly):
    assert features.rebase(monthly, "2020-01-01").iloc[0] == pytest.approx(100)


def test_yoy(monthly):
    assert features.yoy(monthly).iloc[12] == pytest.approx(12.0)


def test_recession_spans():
    idx = pd.date_range("2000-01-01", periods=8, freq="MS")
    flag = pd.Series([0, 1, 1, 0, 0, 1, 0, 0], index=idx)
    spans = features.recession_spans(flag)
    assert spans == [(idx[1], idx[2]), (idx[5], idx[5])]


def test_tech_share():
    idx = pd.date_range("2020-01-01", periods=2, freq="MS")
    panel = pd.DataFrame({"CES6054150001": [10, 20], "CES5051800001": [10, 20],
                          "PAYEMS": [1000, 2000]}, index=idx)
    assert features.tech_share(panel).tolist() == [2.0, 2.0]
