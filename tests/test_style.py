import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from techdemand import style


@pytest.mark.parametrize("ylim", [(0.5, 2.3), (0.4, 2.6), (0.0, 37.0), (-8.0, 35.0)])
def test_percent_axis_labels_are_unique_and_exact(ylim):
    fig, ax = plt.subplots()
    ax.set_ylim(*ylim)
    style.percent_axis(ax)
    fig.canvas.draw()
    ticks = [t for t in ax.get_yticks() if ylim[0] <= t <= ylim[1]]
    labels = [ax.yaxis.get_major_formatter()(t, i) for i, t in enumerate(ticks)]
    plt.close(fig)
    assert len(labels) == len(set(labels))
    assert all(round(t, 1) == pytest.approx(t) for t in ticks)


def test_percent_axis_brazilian_format():
    fig, ax = plt.subplots()
    style.percent_axis(ax, decimals=1)
    assert ax.yaxis.get_major_formatter()(1.5, 0) == "1,5%"
    plt.close(fig)
