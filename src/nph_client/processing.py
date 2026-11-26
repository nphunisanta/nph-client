from __future__ import annotations

import pandas as pd


def resample_hourly_rain(df: pd.DataFrame | None) -> pd.DataFrame:
    """Consolida os dados pluviométricos em soma horária acumulada (mm/h)."""
    if df is None or df.empty or not isinstance(df.index, pd.DatetimeIndex):
        return df.copy() if df is not None else pd.DataFrame()

    numeric_cols = df.select_dtypes(include=["number"]).columns
    if numeric_cols.empty:
        return df.copy()

    return df[numeric_cols].resample("1h").sum()


def resample_hourly_level(df: pd.DataFrame | None) -> pd.DataFrame:
    """Consolida os dados de nível do mar na média horária contínua (m)."""
    if df is None or df.empty or not isinstance(df.index, pd.DatetimeIndex):
        return df.copy() if df is not None else pd.DataFrame()

    numeric_cols = df.select_dtypes(include=["number"]).columns
    if numeric_cols.empty:
        return df.copy()

    return df[numeric_cols].resample("1h").mean()