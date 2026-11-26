from datetime import timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from nph_client import NPHAPIError, NPHAuthError, NPHClient
from nph_client.glossary import resolve_model_id, resolve_param_id


def _mock_response(
    json_data=None,
    status_code=200,
    ok=True,
    text="",
    content_type="application/json",
):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = ok
    resp.text = text
    resp.headers = {"Content-Type": content_type}
    resp.json.return_value = json_data
    return resp


def test_missing_api_key_raises_auth_error(monkeypatch):
    monkeypatch.delenv("NPH_API_KEY", raising=False)
    client = NPHClient()
    with pytest.raises(NPHAuthError):
        client.get_stations()


def test_env_api_key_is_loaded(monkeypatch):
    monkeypatch.setenv("NPH_API_KEY", "env-secret-key")
    client = NPHClient()
    assert client.api_key == "env-secret-key"


def test_health_handles_plain_text_ok(monkeypatch):
    monkeypatch.delenv("NPH_API_KEY", raising=False)
    client = NPHClient()

    with patch.object(
        client._session,
        "get",
        return_value=_mock_response(
            text="ok",
            content_type="text/html; charset=utf-8",
        ),
    ) as mock_get:
        result = client.health()

    assert result == {"status": "ok"}
    headers = mock_get.call_args.kwargs["headers"]
    assert "apiKey" not in headers


def test_http_401_raises_auth_error():
    client = NPHClient("invalid-key")
    with patch.object(
        client._session,
        "get",
        return_value=_mock_response({}, status_code=401, ok=False, text="Unauthorized"),
    ):
        with pytest.raises(NPHAuthError):
            client.get_stations()


def test_http_500_raises_api_error():
    client = NPHClient("valid-key")
    with patch.object(
        client._session,
        "get",
        return_value=_mock_response({}, status_code=500, ok=False, text="Server Error"),
    ):
        with pytest.raises(NPHAPIError) as exc_info:
            client.get_stations()
        assert exc_info.value.status_code == 500


def test_get_stations_returns_indexed_dataframe():
    client = NPHClient("test-key")
    payload = [
        {"id": "351", "station_name": "Palmas", "city_name": "Guarujá"},
        {"id": "411", "station_name": "Praticagem", "city_name": "Santos"},
    ]

    with patch.object(client._session, "get", return_value=_mock_response(payload)):
        df = client.get_stations()

    assert isinstance(df, pd.DataFrame)
    assert list(df.index) == ["351", "411"]
    assert "station_name" in df.columns

def test_measurements_and_forecasts_share_tz_naive_index():
    client = NPHClient("test-key")
    meas_payload = [
        {
            "station_id": "310",
            "station_name": "Cota-200",
            "datetime": "2026-01-01 03:00:00",
            "primary_value": 4.2,
        }
    ]
    fcst_payload = [
        {
            "station_id": "310",
            "station_name": "Cota-200",
            "datetime": "2026-01-01T03:00:00.000Z",
            "value": 3.8,
        }
    ]

    with patch.object(
        client._session,
        "get",
        side_effect=[_mock_response(meas_payload), _mock_response(fcst_payload)],
    ):
        df_m = client.get_measurements(
            stations=[310],
            start_date="2026-01-01",
            end_date="2026-01-02",
            time_offset=timedelta(hours=-3),
        )
        df_f = client.get_forecasts(
            stations=[310],
            model_id="WRF 3km",
            param_id="Precipitação",
            start_date="2026-01-01",
            end_date="2026-01-02",
            time_offset=timedelta(hours=-3),
        )

    assert df_m.index.tz is None
    assert df_f.index.tz is None
    assert df_m.index[0] == df_f.index[0] == pd.Timestamp("2026-01-01 00:00:00")

def test_get_measurements_primary_and_time_offset():
    client = NPHClient("test-key")
    payload = [
        {
            "station_id": "351",
            "station_name": "Palmas",
            "datetime": "2025-12-12 03:00:00",
            "primary_value": 1.32,
            "secondary_value": None,
        },
        {
            "station_id": "351",
            "station_name": "Palmas",
            "datetime": "2025-12-12 04:00:00",
            "primary_value": 1.45,
            "secondary_value": None,
        },
    ]

    with patch.object(client._session, "get", return_value=_mock_response(payload)):
        df = client.get_measurements(
            stations=[351],
            start_date="2025-12-12",
            end_date="2025-12-13",
            return_value=0,
            time_offset=timedelta(hours=-3),
        )

    assert list(df.columns) == ["Palmas"]
    assert df.index[0] == pd.Timestamp("2025-12-12 00:00:00")
    assert df.loc[pd.Timestamp("2025-12-12 01:00:00"), "Palmas"] == pytest.approx(1.45)


def test_get_measurements_extra_values():
    client = NPHClient("test-key")
    payload = [
        {
            "station_id": "411",
            "station_name": "Palmas",
            "datetime": "2025-12-12 00:00:00",
            "extra_values": {"wind_dir": 99.78, "max_temp_C": 28.5},
        }
    ]

    with patch.object(client._session, "get", return_value=_mock_response(payload)):
        df = client.get_measurements(
            stations=411,
            start_date="2025-12-12",
            end_date="2025-12-13",
            return_value=3,
        )

    assert "wind_dir" in df.columns
    assert "max_temp_C" in df.columns
    assert df.iloc[0]["wind_dir"] == pytest.approx(99.78)


def test_get_forecasts_accepts_glossary_names():
    client = NPHClient("test-key")
    payload = [
        {
            "station_id": "351",
            "station_name": "Palmas",
            "datetime": "2025-12-12T00:00:00Z",
            "value": 1.25,
        }
    ]

    with patch.object(
        client._session, "get", return_value=_mock_response(payload)
    ) as mock_get:
        df = client.get_forecasts(
            stations=[351],
            model_id="MOHID",
            param_id="Nível do Mar",
            start_date="2025-12-12",
            end_date="2025-12-13",
        )

    params = mock_get.call_args.kwargs["params"]
    assert params["modelId"] == "4"
    assert params["paramId"] == "13"
    assert df.iloc[0]["Palmas"] == pytest.approx(1.25)


def test_glossary_resolvers():
    assert resolve_model_id("NALA Best") == 20
    assert resolve_param_id("Altura Significativa das Ondas (Hs)") == 16
    with pytest.raises(ValueError):
        resolve_model_id("Modelo Inexistente")
    with pytest.raises(ValueError):
        resolve_param_id("Parametro Inexistente")