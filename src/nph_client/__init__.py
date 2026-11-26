from .charts import (
    plot_chuva,
    plot_combinado_nivel_precipitacao,
    plot_medido_previsao,
    plot_nivel_mar,
)
from .client import NPHClient
from .exceptions import NPHAPIError, NPHAuthError, NPHClientError
from .glossary import MODELS_GLOSSARY, PARAMS_GLOSSARY
from .plotting import AxisConfig, plot_series
from .processing import resample_hourly_level, resample_hourly_rain
from .thresholds import (
    PPDC_THRESHOLD_ALERTA,
    PPDC_THRESHOLD_ATENCAO,
    Threshold,
    get_ppdc_sea_level_thresholds,
)

__version__ = "1.0.2"

__all__ = [
    "__version__",
    "NPHClient",
    "NPHClientError",
    "NPHAuthError",
    "NPHAPIError",
    "MODELS_GLOSSARY",
    "PARAMS_GLOSSARY",
    "Threshold",
    "PPDC_THRESHOLD_ATENCAO",
    "PPDC_THRESHOLD_ALERTA",
    "get_ppdc_sea_level_thresholds",
    "AxisConfig",
    "plot_series",
    "resample_hourly_rain",
    "resample_hourly_level",
    "plot_nivel_mar",
    "plot_chuva",
    "plot_combinado_nivel_precipitacao",
    "plot_medido_previsao",
]