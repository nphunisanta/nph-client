from __future__ import annotations

MODELS_GLOSSARY: dict[str, int] = {
    # Atmosféricos
    "WRF 3km": 1,
    "WRF 1km": 2,
    "ECMWF 9km": 3,
    "WRF 7km": 13,
    "GFS 25km": 15,
    # Hidrodinâmicos e Ondas
    "MOHID": 4,
    "Delft - FLOW (BAIXADA)": 5,
    "Delft - WAVE (BAIXADA)": 6,
    "Delft - FLOW (SESSV)": 7,
    "Delft - WAVE (SESSV)": 8,
    "SWAN v1": 9,
    "SWAN v2": 10,
    "CMS - Hydro Hourly": 11,
    "CMS - Wave": 12,
    "NALA 10min": 17,
    "NALA 1h": 18,
    "NALA 3h": 19,
    "NALA Best": 20,
}

PARAMS_GLOSSARY: dict[str, int] = {
    "Temperatura": 1,
    "Precipitação": 2,
    "Pressão": 3,
    "Rajada de Vento": 4,
    "Velocidade do Vento": 5,
    "Direção do Vento": 6,
    "CAPE": 7,
    "LIFT": 8,
    "Umidade Relativa": 9,
    "Cobertura Total de Nuvens": 10,
    "Ponto de Orvalho": 11,
    "Precipitação Convectiva": 12,
    "Nível do Mar": 13,
    "Direção da Corrente": 14,
    "Velocidade da Corrente": 15,
    "Altura Significativa das Ondas (Hs)": 16,
    "Direção média das ondas": 17,
    "Período de Pico (Tp)": 18,
    "Direção de Pico das Ondas": 19,
}


def resolve_param_id(param_id: int | str) -> int:
    """Resolve um ID inteiro, nome exato ou apelido comum de variável para o ID do glossário."""
    if isinstance(param_id, int):
        return param_id

    text = str(param_id).strip()
    if text.isdigit():
        return int(text)

    low = text.lower()
    for name, pid in PARAMS_GLOSSARY.items():
        if name.lower() == low:
            return pid

    if any(k in low for k in ("chuva", "precip", "rain")):
        return 2
    if any(k in low for k in ("mar", "nivel", "nível", "mare", "maré", "tide", "sea level")):
        return 13
    if "temp" in low:
        return 1
    if "press" in low:
        return 3
    if "rajada" in low or "gust" in low:
        return 4
    if "vento" in low or "wind" in low:
        return 5
    if any(k in low for k in ("onda", "wave", "hs")):
        return 16
    if "corrente" in low or "current" in low:
        return 15

    raise ValueError(
        f"Parâmetro desconhecido: '{param_id}'. "
        "Informe o ID inteiro ou um nome válido do glossário."
    )


def resolve_model_id(model_id: int | str) -> int:
    """Resolve um ID inteiro, nome exato ou apelido comum de modelo para o ID do glossário."""
    if isinstance(model_id, int):
        return model_id

    text = str(model_id).strip()
    if text.isdigit():
        return int(text)

    low = text.lower()
    for name, mid in MODELS_GLOSSARY.items():
        if name.lower() == low:
            return mid

    if "mohid" in low:
        return 4
    if "delft" in low:
        if "wave" in low and "sessv" in low:
            return 8
        if "wave" in low:
            return 6
        if "sessv" in low:
            return 7
        return 5
    if "nala" in low:
        if "10" in low:
            return 17
        if "3h" in low:
            return 19
        if "1h" in low:
            return 18
        return 20
    if "wrf" in low:
        if "1km" in low:
            return 2
        if "7km" in low:
            return 13
        return 1
    if "ecmwf" in low:
        return 3
    if "gfs" in low:
        return 15
    if "swan" in low:
        return 10 if "v2" in low else 9
    if "cms" in low:
        return 12 if "wave" in low else 11

    raise ValueError(
        f"Modelo desconhecido: '{model_id}'. "
        "Informe o ID inteiro ou um nome válido do glossário."
    )