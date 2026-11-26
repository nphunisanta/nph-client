from __future__ import annotations

import logging
import os
import time
from datetime import date, datetime, timedelta
from typing import Any, Sequence

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import NPHAPIError, NPHAuthError
from .glossary import resolve_model_id, resolve_param_id

logger = logging.getLogger(__name__)

StationInput = Sequence[str | int] | str | int
DateInput = str | date | datetime


class NPHClient:
    """Cliente oficial para consumo da API hidro-meteoceanográfica do NPH-UNISANTA."""

    DEFAULT_BASE_URL = "https://nph.unisanta.br/ssbs/api"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("NPH_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def _get_headers(self, require_auth: bool = True) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["apiKey"] = self.api_key
        elif require_auth:
            raise NPHAuthError(
                "API key não informada. Passe `api_key` ao instanciar NPHClient "
                "ou defina a variável de ambiente NPH_API_KEY."
            )
        return headers

    def _request_json(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        require_auth: bool = True,
    ) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers(require_auth=require_auth)

        try:
            response = self._session.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise NPHAPIError(f"Falha de conexão com {url}: {exc}") from exc

        if response.status_code in (401, 403):
            raise NPHAuthError(
                f"Autenticação rejeitada pela API (HTTP {response.status_code}). "
                "Verifique se sua apiKey é válida."
            )

        if not response.ok:
            raise NPHAPIError(
                f"Erro na requisição GET {endpoint} (HTTP {response.status_code}): "
                f"{response.text[:200]}",
                status_code=response.status_code,
            )

        return response.json()

    @staticmethod
    def _normalize_stations(stations: StationInput) -> list[str]:
        if isinstance(stations, (str, int)):
            parts = str(stations).split(",")
            return [p.strip() for p in parts if p.strip()]
        return [str(s).strip() for s in stations if str(s).strip()]

    @staticmethod
    def _to_timestamp(value: DateInput) -> pd.Timestamp:
        ts = pd.to_datetime(value)
        if pd.isna(ts):
            raise ValueError(f"Data inválida: {value!r}")
        return ts

    @staticmethod
    def _format_api_date(ts: pd.Timestamp) -> str:
        if ts.hour == 0 and ts.minute == 0 and ts.second == 0:
            return ts.strftime("%Y-%m-%d")
        return ts.strftime("%Y-%m-%d %H:%M:%S")

    def _fetch_chunked(
        self,
        endpoint: str,
        start_dt: pd.Timestamp,
        end_dt: pd.Timestamp,
        base_params: dict[str, Any],
        chunk_days: int = 365,
    ) -> pd.DataFrame:
        if start_dt > end_dt:
            raise ValueError("`start_date` não pode ser posterior a `end_date`.")

        frames: list[pd.DataFrame] = []

        if start_dt == end_dt:
            params = {
                **base_params,
                "startDate": self._format_api_date(start_dt),
                "endDate": self._format_api_date(end_dt),
            }
            data = self._request_json(endpoint, params=params)
            return pd.DataFrame(data) if data else pd.DataFrame()

        current_start = start_dt
        while current_start < end_dt:
            chunk_end = min(current_start + timedelta(days=chunk_days), end_dt)
            params = {
                **base_params,
                "startDate": self._format_api_date(current_start),
                "endDate": self._format_api_date(chunk_end),
            }
            data = self._request_json(endpoint, params=params)
            if data:
                frames.append(pd.DataFrame(data))

            current_start = chunk_end
            if current_start < end_dt:
                time.sleep(0.05)

        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    # ------------------------------------------------------------------
    # Endpoints públicos
    # ------------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """Verifica se a API está online (endpoint público `/health`)."""
        return self._request_json("health", require_auth=False)

    def get_stations(self) -> pd.DataFrame:
        """Retorna um DataFrame com todas as estações cadastradas na base."""
        data = self._request_json("stations")
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if "id" in df.columns:
            df = df.set_index("id")
        return df

    def get_sources(self) -> dict[str, Any]:
        """Retorna as fontes de dados disponíveis (`models` e `real_data`)."""
        return self._request_json("sources")

    def get_params(self) -> pd.DataFrame:
        """Retorna um DataFrame com os parâmetros físicos disponíveis e suas unidades."""
        data = self._request_json("params")
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if "id" in df.columns:
            df = df.set_index("id")
        return df

    def get_measurements(
        self,
        stations: StationInput,
        start_date: DateInput,
        end_date: DateInput,
        return_value: int = 0,
        time_offset: timedelta | None = None,
    ) -> pd.DataFrame:
        """
        Consulta medições oficiais verificadas pela equipe do NPH.

        Parâmetros
        ----------
        stations : list[str | int] | str | int
            ID de uma estação ou lista de IDs.
        start_date : str | date | datetime
            Data de início da série temporal.
        end_date : str | date | datetime
            Data final da série temporal.
        return_value : int, default 0
            Variável de retorno:
            - 0: `primary_value`
            - 1: `secondary_value`
            - 3: `extra_values` (sensores multivariáveis como estações meteorológicas e ADCPs)
        time_offset : timedelta | None, default None
            Ajuste de fuso horário aplicado ao índice `datetime` (ex: `timedelta(hours=-3)`).
        """
        station_list = self._normalize_stations(stations)
        if not station_list:
            raise ValueError("Informe ao menos um ID de estação em `stations`.")

        start_dt = self._to_timestamp(start_date)
        end_dt = self._to_timestamp(end_date)

        frames: list[pd.DataFrame] = []
        for idx, st_id in enumerate(station_list):
            sub_df = self._fetch_chunked(
                endpoint="measurements",
                start_dt=start_dt,
                end_dt=end_dt,
                base_params={"stationId": st_id},
            )
            if not sub_df.empty:
                frames.append(sub_df)
            if idx < len(station_list) - 1:
                time.sleep(0.05)

        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)
        df["datetime"] = pd.to_datetime(df["datetime"])
        if time_offset is not None:
            df["datetime"] = df["datetime"] + time_offset

        col_name = "station_name" if "station_name" in df.columns else "station_id"

        # Modo multivariável (extra_values)
        if return_value in (2, 3):
            if "extra_values" not in df.columns:
                return pd.DataFrame()

            valid = df.dropna(subset=["extra_values"]).copy()
            if valid.empty:
                return pd.DataFrame()

            normalized = pd.json_normalize(valid["extra_values"])
            normalized.index = valid["datetime"].values
            normalized.index.name = "datetime"

            if valid[col_name].nunique() > 1:
                normalized[col_name] = valid[col_name].values
                return normalized.set_index(col_name, append=True).sort_index()

            return normalized.groupby(level=0).mean(numeric_only=True).sort_index()

        value_col = "secondary_value" if return_value == 1 else "primary_value"
        if value_col not in df.columns:
            return pd.DataFrame()

        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        df_pivot = df.pivot_table(
            index="datetime",
            columns=col_name,
            values=value_col,
            aggfunc="mean",
        )
        return df_pivot.sort_index()

    def get_forecasts(
        self,
        stations: StationInput,
        model_id: int | str,
        param_id: int | str,
        start_date: DateInput,
        end_date: DateInput,
        time_offset: timedelta | None = None,
    ) -> pd.DataFrame:
        """
        Consulta previsões de modelos numéricos verificados pelo NPH.

        Parâmetros
        ----------
        stations : list[str | int] | str | int
            ID de uma estação ou lista de IDs.
        model_id : int | str
            ID ou nome do modelo numérico (consulte o Glossário).
        param_id : int | str
            ID ou nome da variável física (consulte o Glossário).
        start_date : str | date | datetime
            Data de início da consulta.
        end_date : str | date | datetime
            Data final da consulta.
        time_offset : timedelta | None, default None
            Ajuste opcional de fuso horário aplicado ao índice `datetime`.
        """
        station_list = self._normalize_stations(stations)
        if not station_list:
            raise ValueError("Informe ao menos um ID de estação em `stations`.")

        resolved_model = resolve_model_id(model_id)
        resolved_param = resolve_param_id(param_id)
        start_dt = self._to_timestamp(start_date)
        end_dt = self._to_timestamp(end_date)

        frames: list[pd.DataFrame] = []
        for idx, st_id in enumerate(station_list):
            sub_df = self._fetch_chunked(
                endpoint="forecasts",
                start_dt=start_dt,
                end_dt=end_dt,
                base_params={
                    "stationId": st_id,
                    "modelId": str(resolved_model),
                    "paramId": str(resolved_param),
                },
            )
            if not sub_df.empty:
                frames.append(sub_df)
            if idx < len(station_list) - 1:
                time.sleep(0.05)

        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)
        df["datetime"] = pd.to_datetime(df["datetime"])
        if time_offset is not None:
            df["datetime"] = df["datetime"] + time_offset

        col_name = "station_name" if "station_name" in df.columns else "station_id"
        value_col = "value" if "value" in df.columns else df.columns[-1]
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

        df_pivot = df.pivot_table(
            index="datetime",
            columns=col_name,
            values=value_col,
            aggfunc="mean",
        )
        return df_pivot.sort_index()