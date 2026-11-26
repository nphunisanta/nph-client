from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .thresholds import Threshold

logger = logging.getLogger(__name__)

PALETTE_MAP: dict[str, list[str]] = {
    "Ocean": ["#0077b6", "#00b4d8", "#03045e", "#0096c7", "#48cae4"],
    "default": [
        "#0077b6",
        "#e63946",
        "#2a9d8f",
        "#e76f51",
        "#7209b7",
        "#00b4d8",
        "#f4a261",
        "#457b9d",
    ],
}


@dataclass
class AxisConfig:
    """Configurações visuais de um eixo Y para `plot_series`."""

    label: str = ""
    columns: list[str] | None = None
    plot_type: Literal["line", "scatter", "bar", "area"] = "line"
    min_val: float | None = None
    max_val: float | None = None
    step: float | None = None
    thresholds: list[Threshold] = field(default_factory=list)
    plot_kwargs: dict[str, Any] = field(default_factory=dict)
    show_peaks: bool = False
    peak_prefix: str = ""
    show_zeroline: bool = False
    invert_yaxis: bool = False
    custom_colors: list[str] | None = None
    color_palette: str = "default"


def _compute_bar_width(index: pd.Index) -> float:
    """Calcula largura proporcional (em dias, padrão Matplotlib) para séries temporais."""
    if isinstance(index, pd.DatetimeIndex) and len(index) > 1:
        deltas = index.to_series().diff().dropna().dt.total_seconds()
        positive = deltas[deltas > 0]
        if not positive.empty:
            min_days = float(positive.min()) / 86400.0
            return min_days * 0.72
    return (1.0 / 24.0) * 0.72


def _annotate_peaks(
    ax: Axes,
    series: pd.Series,
    color: str | None = None,
    prefix: str = "",
) -> None:
    clean = series.dropna()
    if clean.empty:
        return

    max_date = clean.idxmax()
    max_val = float(clean.max())
    min_date = clean.idxmin()
    min_val = float(clean.min())

    marker_color = color or "#111111"

    ax.scatter(
        [max_date],
        [max_val],
        color=marker_color,
        edgecolors="black",
        linewidths=0.8,
        s=36,
        zorder=5,
    )
    ax.annotate(
        f"{prefix}Máx: {max_val:.2f}",
        xy=(max_date, max_val),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
        color="#111111",
    )

    if min_date != max_date:
        ax.scatter(
            [min_date],
            [min_val],
            color=marker_color,
            edgecolors="black",
            linewidths=0.7,
            s=30,
            zorder=5,
        )
        ax.annotate(
            f"{prefix}Mín: {min_val:.2f}",
            xy=(min_date, min_val),
            xytext=(0, -12),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=8,
            color="#475569",
        )


def _plot_on_axis(ax: Axes, df: pd.DataFrame, conf: AxisConfig) -> None:
    if df is None or df.empty:
        return

    cols = conf.columns if conf.columns else list(df.columns)
    palette = conf.custom_colors or PALETTE_MAP.get(
        conf.color_palette, PALETTE_MAP["default"]
    )

    for idx, col in enumerate(cols):
        if col not in df.columns:
            logger.warning("Coluna '%s' não encontrada no DataFrame.", col)
            continue

        series = df[col].dropna()
        if series.empty:
            continue

        kwargs = dict(conf.plot_kwargs)
        kwargs.setdefault("label", str(col))
        if "color" not in kwargs and "c" not in kwargs:
            kwargs["color"] = palette[idx % len(palette)]

        chosen_color = kwargs.get("color")

        if conf.plot_type == "scatter":
            ax.scatter(series.index, series.values, **kwargs)
        elif conf.plot_type == "bar":
            kwargs.setdefault("width", _compute_bar_width(series.index))
            kwargs.setdefault("alpha", 0.75)
            ax.bar(series.index, series.values, **kwargs)
        elif conf.plot_type == "area":
            fill_alpha = kwargs.pop("alpha", 0.3)
            ax.plot(series.index, series.values, **kwargs)
            ax.fill_between(
                series.index,
                series.values,
                alpha=fill_alpha,
                color=chosen_color,
            )
        else:
            kwargs.setdefault("linewidth", 1.8)
            ax.plot(series.index, series.values, **kwargs)

        if conf.show_peaks and conf.plot_type != "bar":
            _annotate_peaks(ax, series, color=chosen_color, prefix=conf.peak_prefix)

    if conf.label:
        ax.set_ylabel(conf.label, fontweight="bold")

    if conf.show_zeroline:
        ax.axhline(0.0, color="#64748b", linewidth=1.0, alpha=0.65, zorder=1)

    # Limites e espaçamento do eixo Y
    if conf.min_val is not None or conf.max_val is not None:
        current_min, current_max = ax.get_ylim()
        ax.set_ylim(
            bottom=conf.min_val if conf.min_val is not None else current_min,
            top=conf.max_val if conf.max_val is not None else current_max,
        )

    if conf.step is not None and conf.step > 0:
        ax.yaxis.set_major_locator(mticker.MultipleLocator(conf.step))

    # Limiares (calculados antes da inversão do eixo)
    y_top = max(ax.get_ylim())
    for threshold in conf.thresholds:
        ax.axhline(
            y=threshold.value,
            color=threshold.color,
            linestyle=threshold.linestyle,
            linewidth=threshold.linewidth,
            label=threshold.label or None,
        )
        if threshold.fill_above and y_top > threshold.value:
            span_top = (
                min(threshold.max_fill_value, y_top)
                if threshold.max_fill_value is not None
                else y_top
            )
            if span_top > threshold.value:
                ax.axhspan(
                    ymin=threshold.value,
                    ymax=span_top,
                    color=threshold.color,
                    alpha=threshold.alpha,
                    zorder=0,
                )

    if conf.invert_yaxis:
        ax.invert_yaxis()


def plot_series(
    df: pd.DataFrame | list[pd.DataFrame],
    primary_conf: AxisConfig,
    secondary_conf: AxisConfig | None = None,
    title: str = "",
    x_lim: bool | tuple[Any, Any] = False,
    figsize: tuple[float, float] = (12, 6),
    save_path: str | None = None,
) -> Figure:
    """
    Gera visualização gráfica em Matplotlib combinando um ou dois DataFrames
    com configurações independentes para eixo primário e secundário.
    """
    if isinstance(df, list):
        df_primary = df[0] if len(df) > 0 else pd.DataFrame()
        df_secondary = df[1] if len(df) > 1 else df_primary
    else:
        df_primary = df
        df_secondary = df

    fig, ax1 = plt.subplots(figsize=figsize)
    ax1.grid(True, linestyle=":", alpha=0.5)

    _plot_on_axis(ax1, df_primary, primary_conf)

    handles, labels = ax1.get_legend_handles_labels()

    if secondary_conf is not None:
        ax2 = ax1.twinx()
        _plot_on_axis(ax2, df_secondary, secondary_conf)
        h2, l2 = ax2.get_legend_handles_labels()
        handles.extend(h2)
        labels.extend(l2)

    # Ajuste do eixo X
    if isinstance(x_lim, tuple) and len(x_lim) == 2:
        ax1.set_xlim(x_lim[0], x_lim[1])
    elif x_lim is True:
        indices = [
            d.index
            for d in (df_primary, df_secondary)
            if d is not None and not d.empty
        ]
        if indices:
            min_x = min(idx.min() for idx in indices)
            max_x = max(idx.max() for idx in indices)
            if min_x != max_x:
                ax1.set_xlim(min_x, max_x)

    # Formatação de datas para índices temporais
    if isinstance(df_primary.index, pd.DatetimeIndex) or (
        secondary_conf is not None and isinstance(df_secondary.index, pd.DatetimeIndex)
    ):
        locator = mdates.AutoDateLocator()
        ax1.xaxis.set_major_locator(locator)
        ax1.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    if title:
        ax1.set_title(title, fontweight="bold", pad=12)

    if handles:
        ax1.legend(handles, labels, loc="best", frameon=True)

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig