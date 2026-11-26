import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from nph_client import (
    AxisConfig,
    Threshold,
    get_ppdc_sea_level_thresholds,
    plot_chuva,
    plot_combinado_nivel_precipitacao,
    plot_medido_previsao,
    plot_nivel_mar,
    plot_series,
    resample_hourly_level,
    resample_hourly_rain,
)


def _sample_df(col_name: str, values: list[float], freq: str = "1h") -> pd.DataFrame:
    idx = pd.date_range("2025-12-12 00:00:00", periods=len(values), freq=freq)
    return pd.DataFrame({col_name: values}, index=idx)


def test_ppdc_thresholds():
    thresholds = get_ppdc_sea_level_thresholds()
    assert len(thresholds) == 2
    assert thresholds[0].value == 1.8
    assert thresholds[1].value == 2.0


def test_resampling_helpers():
    df_rain = _sample_df("Santos", [1.0, 2.0, 3.0, 4.0], freq="30min")
    hourly_rain = resample_hourly_rain(df_rain)
    assert hourly_rain.iloc[0]["Santos"] == 3.0
    assert hourly_rain.iloc[1]["Santos"] == 7.0

    df_level = _sample_df("Palmas", [1.0, 2.0, 2.0, 4.0], freq="30min")
    hourly_level = resample_hourly_level(df_level)
    assert hourly_level.iloc[0]["Palmas"] == 1.5
    assert hourly_level.iloc[1]["Palmas"] == 3.0


def test_plot_series_single_axis():
    df = _sample_df("Palmas", [1.1, 1.4, 1.9, 2.1])
    conf = AxisConfig(
        label="Nível do Mar (m)",
        columns=["Palmas"],
        plot_type="scatter",
        min_val=0.0,
        max_val=2.5,
        step=0.5,
        thresholds=[
            Threshold(value=1.8, color="orange", label="ATENÇÃO", fill_above=True),
            Threshold(value=2.0, color="red", label="ALERTA", fill_above=True),
        ],
    )

    fig = plot_series(df=df, primary_conf=conf, title="Teste Único", x_lim=True)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_plot_series_dual_axis_and_save(tmp_path):
    df_meas = _sample_df("Palmas", [1.0, 1.5, 1.9, 1.7])
    df_fcst = _sample_df("Delft", [1.1, 1.4, 1.85, 1.6])

    primary = AxisConfig(
        plot_type="scatter",
        label="Nível do Mar (m)",
        columns=["Palmas"],
        min_val=-0.5,
        max_val=2.5,
        step=0.5,
        plot_kwargs={"marker": "8", "s": 4, "color": "black"},
    )
    secondary = AxisConfig(
        plot_type="line",
        label="Previsão (m)",
        columns=["Delft"],
        min_val=-0.5,
        max_val=2.5,
        step=0.5,
        plot_kwargs={"linewidth": 1.5, "color": "green"},
    )

    output_file = tmp_path / "plot_test.png"
    fig = plot_series(
        df=[df_meas, df_fcst],
        primary_conf=primary,
        secondary_conf=secondary,
        title="Comparação Medido vs Previsto",
        x_lim=True,
        save_path=str(output_file),
    )

    assert isinstance(fig, Figure)
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    plt.close(fig)


def test_high_level_charts():
    df_nivel = _sample_df("Praticagem", [1.2, 1.6, 2.05, 1.5])
    df_prev = _sample_df("Praticagem", [1.1, 1.55, 1.95, 1.4])
    df_chuva = _sample_df("Vila Mathias", [0.0, 4.5, 12.0, 2.5])

    fig1 = plot_nivel_mar(df=df_nivel)
    fig2 = plot_chuva(df=df_chuva)
    fig3 = plot_combinado_nivel_precipitacao(df_nivel=df_nivel, df_chuva=df_chuva)
    fig4 = plot_medido_previsao(df_medido=df_nivel, df_previsao=df_prev)

    for fig in (fig1, fig2, fig3, fig4):
        assert isinstance(fig, Figure)
        plt.close(fig)