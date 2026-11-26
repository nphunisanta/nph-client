from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from matplotlib.figure import Figure

from .client import NPHClient
from .plotting import AxisConfig, PALETTE_MAP, _annotate_peaks, plot_series
from .processing import resample_hourly_level, resample_hourly_rain
from .thresholds import Threshold, get_ppdc_sea_level_thresholds

StationInput = Sequence[str | int] | str | int
DateInput = str | date | datetime


def _is_forecast_mode(tipo_dado: str) -> bool:
    return str(tipo_dado).lower().strip() in {"previsto", "previsao", "previsão", "forecast"}


def _apply_offset(df: pd.DataFrame, offset: float) -> pd.DataFrame:
    if offset == 0.0 or df.empty:
        return df
    out = df.copy()
    num_cols = out.select_dtypes(include=["number"]).columns
    out[num_cols] = out[num_cols] + offset
    return out


def _fetch_series(
    client: NPHClient,
    stations: StationInput,
    start_date: DateInput | None,
    end_date: DateInput | None,
    is_forecast: bool,
    model_id: int | str,
    param_id: int | str,
    time_offset: timedelta | None,
) -> pd.DataFrame:
    start = start_date or (date.today() - timedelta(days=7))
    end = end_date or (
        datetime.now() + timedelta(days=3) if is_forecast else datetime.now()
    )
    if is_forecast:
        return client.get_forecasts(
            stations=stations,
            model_id=model_id,
            param_id=param_id,
            start_date=start,
            end_date=end,
            time_offset=time_offset,
        )
    return client.get_measurements(
        stations=stations,
        start_date=start,
        end_date=end,
        time_offset=time_offset,
    )


def plot_nivel_mar(
    df: pd.DataFrame | None = None,
    stations: StationInput | None = None,
    start_date: DateInput | None = None,
    end_date: DateInput | None = None,
    tipo_dado: str = "medido",
    model: int | str = "MOHID",
    api_key: str | None = None,
    client: NPHClient | None = None,
    columns: list[str] | None = None,
    title: str | None = None,
    thresholds: list[Threshold] | None = None,
    show_thresholds: bool = True,
    show_peaks: bool = True,
    show_zeroline: bool = False,
    offset: float = 0.0,
    offset_mare: float | None = None,
    y_range: tuple[float, float] | None = None,
    time_offset: timedelta | None = timedelta(hours=-3),
    figsize: tuple[float, float] = (14, 6),
    save_path: str | None = None,
) -> Figure:
    """Plota série temporal de nível do mar com picos e limiares do PPDC Ressacas."""
    if offset_mare is not None:
        offset = offset_mare

    is_forecast = _is_forecast_mode(tipo_dado)

    if df is None:
        if stations is None:
            raise ValueError("Informe `df` ou `stations` para gerar o gráfico de nível do mar.")
        cli = client or NPHClient(api_key=api_key)
        df = _fetch_series(
            client=cli,
            stations=stations,
            start_date=start_date,
            end_date=end_date,
            is_forecast=is_forecast,
            model_id=model,
            param_id="Nível do Mar",
            time_offset=time_offset,
        )

    if df.empty:
        raise ValueError("Nenhum dado encontrado para gerar o gráfico de Nível do Mar.")

    df = _apply_offset(df, offset)

    if title is None:
        title = (
            f"Nível do Mar - Previsão {model} (NPH-UNISANTA)"
            if is_forecast
            else "Nível do Mar - PPDC Ressacas (NPH-UNISANTA)"
        )

    if not show_thresholds:
        thresholds_to_use: list[Threshold] = []
    elif thresholds is not None:
        thresholds_to_use = thresholds
    else:
        thresholds_to_use = get_ppdc_sea_level_thresholds()

    min_val = y_range[0] if y_range is not None else -2.5
    max_val = y_range[1] if y_range is not None else 2.5

    primary_conf = AxisConfig(
        label="Nível do Mar (m)",
        columns=columns,
        plot_type="line",
        min_val=min_val,
        max_val=max_val,
        step=0.5,
        thresholds=thresholds_to_use,
        show_peaks=show_peaks,
        peak_prefix="Prev " if is_forecast else "",
        show_zeroline=show_zeroline,
        color_palette="Ocean",
    )

    return plot_series(
        df=df,
        primary_conf=primary_conf,
        title=title,
        x_lim=True,
        figsize=figsize,
        save_path=save_path,
    )


def plot_chuva(
    df: pd.DataFrame | None = None,
    stations: StationInput | None = None,
    start_date: DateInput | None = None,
    end_date: DateInput | None = None,
    tipo_dado: str = "medido",
    model: int | str = "WRF 3km",
    api_key: str | None = None,
    client: NPHClient | None = None,
    columns: list[str] | None = None,
    title: str | None = None,
    hourly: bool = True,
    show_zeroline: bool = False,
    y_range: tuple[float, float] | None = None,
    time_offset: timedelta | None = timedelta(hours=-3),
    figsize: tuple[float, float] = (12, 6),
    save_path: str | None = None,
) -> Figure:
    """Plota gráfico de barras de precipitação pluviométrica (mm)."""
    is_forecast = _is_forecast_mode(tipo_dado)

    if df is None:
        if stations is None:
            raise ValueError("Informe `df` ou `stations` para gerar o gráfico de chuva.")
        cli = client or NPHClient(api_key=api_key)
        df = _fetch_series(
            client=cli,
            stations=stations,
            start_date=start_date,
            end_date=end_date,
            is_forecast=is_forecast,
            model_id=model,
            param_id="Precipitação",
            time_offset=time_offset,
        )

    if df.empty:
        raise ValueError("Nenhum dado encontrado para gerar o gráfico de Chuva.")

    if hourly:
        df = resample_hourly_rain(df)

    if title is None:
        title = (
            f"Precipitação Pluviométrica - Previsão {model} (NPH-UNISANTA)"
            if is_forecast
            else "Precipitação Pluviométrica (NPH-UNISANTA)"
        )

    min_val = y_range[0] if y_range is not None else 0.0
    max_val = y_range[1] if y_range is not None else None

    primary_conf = AxisConfig(
        label="Precipitação (mm)",
        columns=columns,
        plot_type="bar",
        min_val=min_val,
        max_val=max_val,
        show_zeroline=show_zeroline,
        custom_colors=["#1f77b4", "#0096c7", "#03045e"],
        plot_kwargs={"alpha": 0.8},
    )

    return plot_series(
        df=df,
        primary_conf=primary_conf,
        title=title,
        x_lim=True,
        figsize=figsize,
        save_path=save_path,
    )


def plot_combinado_nivel_precipitacao(
    df_nivel: pd.DataFrame | None = None,
    df_chuva: pd.DataFrame | None = None,
    stations_nivel: StationInput | None = None,
    stations_chuva: StationInput | None = None,
    start_date: DateInput | None = None,
    end_date: DateInput | None = None,
    tipo_dado_nivel: str = "medido",
    tipo_dado_chuva: str = "medido",
    model_nivel: int | str = "MOHID",
    model_chuva: int | str = "WRF 3km",
    api_key: str | None = None,
    client: NPHClient | None = None,
    title: str | None = None,
    level_columns: list[str] | None = None,
    precip_columns: list[str] | None = None,
    thresholds: list[Threshold] | None = None,
    show_thresholds: bool = True,
    show_peaks: bool = True,
    show_zeroline: bool = False,
    hourly_rain: bool = True,
    hourly_level: bool = True,
    offset_nivel: float = 0.0,
    offset_mare: float | None = None,
    invert_rain_axis: bool = True,
    y_range_nivel: tuple[float, float] | None = None,
    y_range_chuva: tuple[float, float] | None = None,
    time_offset: timedelta | None = timedelta(hours=-3),
    figsize: tuple[float, float] = (14, 6),
    save_path: str | None = None,
) -> Figure:
    """Reúne nível do mar (eixo primário) e precipitação (eixo secundário invertido)."""
    if offset_mare is not None:
        offset_nivel = offset_mare

    is_nivel_prev = _is_forecast_mode(tipo_dado_nivel)
    is_chuva_prev = _is_forecast_mode(tipo_dado_chuva)

    cli = client or (
        NPHClient(api_key=api_key)
        if (df_nivel is None or df_chuva is None)
        else None
    )

    if df_nivel is None and cli is not None and stations_nivel is not None:
        df_nivel = _fetch_series(
            client=cli,
            stations=stations_nivel,
            start_date=start_date,
            end_date=end_date,
            is_forecast=is_nivel_prev,
            model_id=model_nivel,
            param_id="Nível do Mar",
            time_offset=time_offset,
        )

    if df_chuva is None and cli is not None and stations_chuva is not None:
        df_chuva = _fetch_series(
            client=cli,
            stations=stations_chuva,
            start_date=start_date,
            end_date=end_date,
            is_forecast=is_chuva_prev,
            model_id=model_chuva,
            param_id="Precipitação",
            time_offset=time_offset,
        )

    if df_nivel is None or df_nivel.empty:
        raise ValueError("O DataFrame de nível do mar está vazio ou não foi encontrado.")
    if df_chuva is None or df_chuva.empty:
        raise ValueError("O DataFrame de chuva está vazio ou não foi encontrado.")

    if hourly_rain:
        df_chuva = resample_hourly_rain(df_chuva)
    if hourly_level:
        df_nivel = resample_hourly_level(df_nivel)

    if (
        hourly_rain
        and hourly_level
        and isinstance(df_nivel.index, pd.DatetimeIndex)
        and isinstance(df_chuva.index, pd.DatetimeIndex)
    ):
        common_start = min(df_nivel.index.min(), df_chuva.index.min())
        common_end = max(df_nivel.index.max(), df_chuva.index.max())
        full_idx = pd.date_range(start=common_start, end=common_end, freq="1h")
        df_nivel = df_nivel.reindex(full_idx)
        df_chuva = df_chuva.reindex(full_idx, fill_value=0.0)

    df_nivel = _apply_offset(df_nivel, offset_nivel)

    if title is None:
        if is_nivel_prev and is_chuva_prev:
            title = f"Gráfico Combinado: Nível ({model_nivel}) e Chuva ({model_chuva}) (NPH-UNISANTA)"
        elif is_nivel_prev:
            title = f"Gráfico Combinado: Nível ({model_nivel}) e Chuva Medida (NPH-UNISANTA)"
        elif is_chuva_prev:
            title = f"Gráfico Combinado: Nível Medido e Chuva ({model_chuva}) (NPH-UNISANTA)"
        else:
            title = "Gráfico Combinado: Nível do Mar e Precipitação (NPH-UNISANTA)"

    if not show_thresholds:
        thresholds_to_use: list[Threshold] = []
    elif thresholds is not None:
        thresholds_to_use = thresholds
    else:
        thresholds_to_use = get_ppdc_sea_level_thresholds()

    min_val_nivel = y_range_nivel[0] if y_range_nivel is not None else -2.5
    max_val_nivel = y_range_nivel[1] if y_range_nivel is not None else 2.5
    min_val_chuva = y_range_chuva[0] if y_range_chuva is not None else 0.0
    max_val_chuva = y_range_chuva[1] if y_range_chuva is not None else None

    primary_conf = AxisConfig(
        label="Nível do Mar (m)",
        columns=level_columns,
        plot_type="line",
        min_val=min_val_nivel,
        max_val=max_val_nivel,
        step=0.5,
        thresholds=thresholds_to_use,
        show_peaks=show_peaks,
        peak_prefix="Prev " if is_nivel_prev else "",
        show_zeroline=show_zeroline,
        color_palette="Ocean",
    )

    secondary_conf = AxisConfig(
        label="Precipitação (mm)",
        columns=precip_columns,
        plot_type="bar",
        min_val=min_val_chuva,
        max_val=max_val_chuva,
        invert_yaxis=invert_rain_axis,
        custom_colors=["#2b5c8f", "#4682b4"],
        plot_kwargs={"alpha": 0.55},
    )

    return plot_series(
        df=[df_nivel, df_chuva],
        primary_conf=primary_conf,
        secondary_conf=secondary_conf,
        title=title,
        x_lim=True,
        figsize=figsize,
        save_path=save_path,
    )


def plot_medido_previsao(
    df_medido: pd.DataFrame | None = None,
    df_previsao: pd.DataFrame | None = None,
    stations: StationInput | None = None,
    start_date: DateInput | None = None,
    end_date: DateInput | None = None,
    api_key: str | None = None,
    client: NPHClient | None = None,
    model_id: int | str = 4,
    model: int | str | None = None,
    param_id: int | str = "Nível do Mar",
    param_label: str = "Nível do Mar (m)",
    title: str | None = None,
    columns_medido: list[str] | None = None,
    columns_previsao: list[str] | None = None,
    color_medido: str | None = None,
    color_previsao: str | None = None,
    show_thresholds: bool = True,
    thresholds: list[Threshold] | None = None,
    show_peaks: bool = True,
    peaks_source: str = "both",
    show_zeroline: bool = False,
    offset: float = 0.0,
    offset_mare: float | None = None,
    offset_medido: float | None = None,
    offset_previsao: float | None = None,
    y_range: tuple[float, float] | None = None,
    step: float | None = None,
    time_offset: timedelta | None = timedelta(hours=-3),
    figsize: tuple[float, float] = (14, 6),
    save_path: str | None = None,
) -> Figure:
    """
    Sobrepõe dados medidos (tracejado) e previsão numérica (sólido)
    no mesmo eixo Y para comparação direta.
    """
    if model is not None:
        model_id = model
    if offset_mare is not None:
        offset = offset_mare
    if offset_medido is None:
        offset_medido = offset
    if offset_previsao is None:
        offset_previsao = 0.0

    cli = client or (
        NPHClient(api_key=api_key)
        if (df_medido is None or df_previsao is None) and stations is not None
        else None
    )

    if df_medido is None and cli is not None and stations is not None:
        df_medido = _fetch_series(
            client=cli,
            stations=stations,
            start_date=start_date,
            end_date=end_date,
            is_forecast=False,
            model_id=model_id,
            param_id=param_id,
            time_offset=time_offset,
        )

    if df_previsao is None and cli is not None and stations is not None:
        df_previsao = _fetch_series(
            client=cli,
            stations=stations,
            start_date=start_date,
            end_date=end_date,
            is_forecast=True,
            model_id=model_id,
            param_id=param_id,
            time_offset=time_offset,
        )

    has_medido = df_medido is not None and not df_medido.empty
    has_previsao = df_previsao is not None and not df_previsao.empty

    if not has_medido and not has_previsao:
        raise ValueError(
            "Nenhum dado medido ou de previsão encontrado para gerar o gráfico comparativo."
        )

    if has_medido:
        df_medido = _apply_offset(df_medido, offset_medido)
    if has_previsao:
        df_previsao = _apply_offset(df_previsao, offset_previsao)

    if title is None:
        title = f"Comparativo: Dado Medido vs Previsão {model_id} (NPH-UNISANTA)"

    cols_m = (columns_medido or list(df_medido.columns)) if has_medido else []
    cols_p = (columns_previsao or list(df_previsao.columns)) if has_previsao else []

    all_stations = list(dict.fromkeys(cols_p + cols_m))
    is_multi = len(all_stations) > 1
    palette = PALETTE_MAP["default"]

    fig, ax = plt.subplots(figsize=figsize)
    ax.grid(True, linestyle=":", alpha=0.5)

    if has_previsao and df_previsao is not None:
        for col in cols_p:
            if col not in df_previsao.columns:
                continue
            series = df_previsao[col].dropna()
            if series.empty:
                continue
            idx = all_stations.index(col)
            c = color_previsao or (palette[idx % len(palette)] if is_multi else "#0077b6")
            label = f"{col} (Previsão)" if not str(col).endswith("(Previsão)") else str(col)
            ax.plot(series.index, series.values, color=c, linewidth=2.0, linestyle="-", label=label)
            if show_peaks and peaks_source in ("both", "previsao"):
                _annotate_peaks(ax, series, color=c, prefix="Prev ")

    if has_medido and df_medido is not None:
        for col in cols_m:
            if col not in df_medido.columns:
                continue
            series = df_medido[col].dropna()
            if series.empty:
                continue
            idx = all_stations.index(col)
            c = color_medido or (palette[idx % len(palette)] if is_multi else "#e63946")
            label = f"{col} (Medido)" if not str(col).endswith("(Medido)") else str(col)
            ax.plot(series.index, series.values, color=c, linewidth=1.8, linestyle="--", label=label)
            if show_peaks and peaks_source in ("both", "medido"):
                _annotate_peaks(ax, series, color=c, prefix="Med ")

    is_sea_level = (
        "nível" in param_label.lower()
        or "nivel" in param_label.lower()
        or param_id in ("Nível do Mar", 13)
    )

    if show_zeroline:
        ax.axhline(0.0, color="#64748b", linewidth=1.0, alpha=0.65, zorder=1)

    if y_range is not None:
        ax.set_ylim(y_range[0], y_range[1])
    elif is_sea_level:
        ax.set_ylim(-2.5, 2.5)

    step_to_use = step if step is not None else (0.5 if is_sea_level else None)
    if step_to_use is not None and step_to_use > 0:
        ax.yaxis.set_major_locator(mticker.MultipleLocator(step_to_use))

    if show_thresholds and (thresholds is not None or is_sea_level):
        active_thresholds = thresholds if thresholds is not None else get_ppdc_sea_level_thresholds()
        y_top = max(ax.get_ylim())
        for t in active_thresholds:
            ax.axhline(
                y=t.value,
                color=t.color,
                linestyle=t.linestyle,
                linewidth=t.linewidth,
                label=t.label or None,
            )
            if t.fill_above and y_top > t.value:
                span_top = min(t.max_fill_value, y_top) if t.max_fill_value is not None else y_top
                if span_top > t.value:
                    ax.axhspan(ymin=t.value, ymax=span_top, color=t.color, alpha=t.alpha, zorder=0)

    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    ax.set_ylabel(param_label, fontweight="bold")
    ax.set_title(title, fontweight="bold", pad=12)
    ax.legend(loc="best", frameon=True)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig