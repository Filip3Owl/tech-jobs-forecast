"""Tema visual escuro (fundo preto) aplicado a todos os gráficos do projeto.

A paleta categórica foi validada (CVD, contraste e separação perceptual)
contra a superfície #0b0b0b. As cores seguem a entidade, nunca a posição:
use `color_for(nome)` para que uma série mantenha a mesma cor em todo o projeto.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

from . import config

SURFACE = "#0b0b0b"
TEXT_PRIMARY = "#f0efec"
TEXT_SECONDARY = "#c3c2b7"
TEXT_MUTED = "#8a8980"
GRID = "#2a2a28"

# Ordem fixa — nunca reciclar cores; acima de 8 séries, agrupar em "Outros".
PALETTE = [
    "#3987e5",  # azul
    "#d95926",  # laranja
    "#199e70",  # verde-água
    "#c98500",  # amarelo
    "#d55181",  # magenta
    "#008300",  # verde
    "#9085e9",  # violeta
    "#e66767",  # vermelho
]
NEUTRAL = "#6b6a64"

# Divergente (queda ↔ crescimento) com ponto médio neutro.
DIVERGING = ["#d95926", "#383835", "#3987e5"]
SEQUENTIAL_BLUE = ["#184f95", "#1c5cab", "#256abf", "#2a78d6", "#3987e5",
                   "#5598e7", "#6da7ec", "#86b6ef", "#9ec5f4"]

_registry: dict[str, str] = {}


def color_for(name: str) -> str:
    """Atribui uma cor fixa a uma entidade na ordem em que ela aparece pela 1ª vez."""
    if name not in _registry:
        _registry[name] = PALETTE[len(_registry) % len(PALETTE)]
    return _registry[name]


def apply() -> None:
    """Aplica o tema escuro globalmente."""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT_SECONDARY,
        "axes.titlecolor": TEXT_PRIMARY,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.labelsize": 10.5,
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": mpl.cycler(color=PALETTE),
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": TEXT_MUTED,
        "ytick.color": TEXT_MUTED,
        "xtick.labelcolor": TEXT_SECONDARY,
        "ytick.labelcolor": TEXT_SECONDARY,
        "text.color": TEXT_PRIMARY,
        "legend.frameon": False,
        "legend.labelcolor": TEXT_SECONDARY,
        "legend.fontsize": 9.5,
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
        "font.family": "sans-serif",
        "font.size": 10.5,
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "image.cmap": "Blues_r",
    })


def subtitle(ax, text: str) -> None:
    """Subtítulo em tom secundário logo abaixo do título do eixo."""
    ax.text(0, 1.015, text, transform=ax.transAxes, color=TEXT_SECONDARY,
            fontsize=10, va="bottom", ha="left")


def source(fig, text: str) -> None:
    """Nota de fonte no rodapé da figura."""
    fig.text(0.01, -0.02, f"Fonte: {text}", color=TEXT_MUTED, fontsize=8.5,
             ha="left", va="top")


def label_line_end(ax, x, y, text: str, color: str, dx: float = 0.0) -> None:
    """Rótulo direto no fim da linha (texto em tinta neutra, marcador colorido)."""
    ax.plot([x], [y], "o", color=color, markersize=6, markeredgecolor=SURFACE,
            markeredgewidth=1.5, zorder=5)
    ax.annotate(text, (x, y), xytext=(6 + dx, 0), textcoords="offset points",
                color=TEXT_SECONDARY, fontsize=9, va="center")


def save(fig, name: str) -> None:
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGURES / f"{name}.png")
