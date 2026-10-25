"""Validações do snapshot de projeções do BLS e do parser JSON-stat."""
import pandas as pd
import pytest

from techdemand.data_sources import _parse_jsonstat, load_bls_projections


@pytest.fixture(scope="module")
def bls():
    return load_bls_projections().set_index("soc_code")


def _children_sum(df, prefix, level, col):
    mask = (df["level"] == level) & df.index.str.startswith(prefix)
    return df.loc[mask, col].sum()


@pytest.mark.parametrize("col", ["employment_2025", "employment_2035"])
def test_soc_hierarchy_sums(bls, col):
    # Grupo maior = computação + matemática
    assert bls.loc["15-0000", col] == pytest.approx(
        bls.loc["15-1200", col] + bls.loc["15-2000", col], abs=0.2)
    # Grupos amplos de computação somam o grupo menor 15-1200
    broad = _children_sum(bls, "15-12", "broad", col) + bls.loc["15-1299", col]
    broad += bls.loc["15-1221", col]  # pesquisa em computação não tem grupo amplo próprio
    assert broad == pytest.approx(bls.loc["15-1200", col], abs=0.5)
    # Ocupações detalhadas somam seus grupos amplos
    for parent in ["15-1210", "15-1230", "15-1240", "15-1250"]:
        kids = _children_sum(bls, parent[:6], "detailed", col)
        assert kids == pytest.approx(bls.loc[parent, col], abs=0.3), parent
    assert _children_sum(bls, "15-20", "detailed", col) == pytest.approx(
        bls.loc["15-2000", col], abs=0.3)


def test_change_pct_consistent_with_levels(bls):
    implied = (bls["employment_2035"] / bls["employment_2025"] - 1) * 100
    # Níveis publicados com 1 casa decimal: o erro de arredondamento pesa mais
    # em ocupações pequenas (ex.: matemáticos, 2,2 mil).
    tolerance = 0.1 + 100 * 0.1 / bls["employment_2025"]
    assert ((implied - bls["change_pct"]).abs() <= tolerance).all()


def test_parse_jsonstat_roundtrip():
    payload = {
        "id": ["unit", "time"],
        "dimension": {
            "unit": {"category": {"index": {"A": 0, "B": 1}}},
            "time": {"category": {"index": {"2020": 0, "2021": 1}}},
        },
        "value": {"0": 1.0, "1": 2.0, "3": 4.0},  # B/2020 ausente
        "status": {"1": "b"},
    }
    df = _parse_jsonstat(payload)
    assert len(df) == 3
    assert df.set_index(["unit", "time"]).loc[("B", "2021"), "value"] == 4.0
    assert ("B", "2020") not in set(zip(df.unit, df.time))
    assert df.set_index(["unit", "time"]).loc[("A", "2021"), "flag"] == "b"
