from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Threshold:
    """Define uma linha horizontal de referência (e faixa opcional acima)."""

    value: float
    color: str = "red"
    label: str = ""
    fill_above: bool = False
    max_fill_value: float | None = None
    alpha: float = 0.15
    linestyle: str = "--"
    linewidth: float = 1.5


PPDC_THRESHOLD_ATENCAO = Threshold(
    value=1.8,
    color="#f39c12",
    label="ATENÇÃO",
    fill_above=True,
    max_fill_value=2.0,
    alpha=0.15,
    linestyle="--",
)

PPDC_THRESHOLD_ALERTA = Threshold(
    value=2.0,
    color="#e74c3c",
    label="ALERTA",
    fill_above=True,
    max_fill_value=None,
    alpha=0.18,
    linestyle="--",
)


def get_ppdc_sea_level_thresholds() -> list[Threshold]:
    """Retorna os limiares padrão de Atenção (1.8m) e Alerta (2.0m) do PPDC Ressacas."""
    return [PPDC_THRESHOLD_ATENCAO, PPDC_THRESHOLD_ALERTA]