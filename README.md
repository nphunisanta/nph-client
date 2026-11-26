# nph-client

[![PyPI version](https://img.shields.io/pypi/v/nph-client.svg)](https://pypi.org/project/nph-client/)
[![Python versions](https://img.shields.io/pypi/pyversions/nph-client.svg)](https://pypi.org/project/nph-client/)
[![Software License: MIT](https://img.shields.io/badge/Code%20License-MIT-blue.svg)](LICENSE)
[![Data License: CC BY-NC 4.0](https://img.shields.io/badge/Data%20License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24142964.svg)](https://doi.org/10.5281/zenodo.24142964)

Biblioteca Python oficial da **Sala de Situação de Recursos Hídricos da Baixada Santista (SS-BS)**, desenvolvida pelo **Núcleo de Pesquisas Hidrodinâmicas da Universidade Santa Cecília (NPH-UNISANTA)** para aquisição e visualização de dados hidro-meteoceanográficos (chuva, nível do mar/rio, ondas, correntes e vento) no litoral de São Paulo.

## Instalação

```bash
pip install nph-client
```

**Requisitos:** Python `3.11+` (`matplotlib`, `numpy`, `pandas`, `requests`).

## Credenciais de Acesso

Para consumir os dados da API, solicite sua chave de acesso (`apiKey`) no portal oficial do NPH-UNISANTA:

- Cadastro e solicitação de chave: **https://nph.unisanta.br/ssbs/request**

Você pode passar a chave diretamente ao inicializar `NPHClient(api_key)` ou configurá-la na variável de ambiente `NPH_API_KEY` (recomendado para não expor credenciais em scripts e notebooks).

## Uso Rápido

### 1. Listar estações disponíveis

```python
from nph_client import NPHClient

client = NPHClient("SUA_API_KEY")
estacoes = client.get_stations()
print(estacoes.head())
```

### 2. Consultar medições observadas

```python
from datetime import timedelta
from nph_client import NPHClient

client = NPHClient("SUA_API_KEY")

df_measurements = client.get_measurements(
    stations=[351],
    start_date="2025-12-12",
    end_date="2025-12-13",
    return_value=0,
    time_offset=timedelta(hours=-3),
)
```

### 3. Consultar previsões de modelos numéricos

```python
df_forecasts = client.get_forecasts(
    stations=[351],
    model_id=4,       # MOHID (aceita ID inteiro ou nome do glossário)
    param_id=13,      # Nível do Mar (aceita ID inteiro ou nome do glossário)
    start_date="2025-12-12",
    end_date="2025-12-13",
)
```

### 4. Gerar gráficos com limiares (`plotter`)

```python
import matplotlib.pyplot as plt
from nph_client.plotting import AxisConfig, Threshold, plot_series

limite_atencao = Threshold(
    value=1.8,
    color="orange",
    label="ESTADO DE ATENÇÃO",
    fill_above=True,
    alpha=0.15,
)

limite_alerta = Threshold(
    value=2.0,
    color="red",
    label="ESTADO DE ALERTA",
    fill_above=True,
)

conf_measurement = AxisConfig(
    plot_type="scatter",
    label="Nível do Mar (m)",
    columns=["Palmas"],
    min_val=-0.5,
    max_val=2.5,
    step=0.5,
    thresholds=[limite_atencao, limite_alerta],
    plot_kwargs={"marker": "8", "s": 4, "alpha": 1, "color": "black"},
)

conf_forecast = AxisConfig(
    label="Nível do Mar (m)",
    columns=["Palmas"],
    min_val=-0.5,
    max_val=2.5,
    step=0.5,
    plot_kwargs={"alpha": 1, "linewidth": 1.5, "color": "green"},
)

plot_series(
    df=[df_measurements, df_forecasts],
    primary_conf=conf_measurement,
    secondary_conf=conf_forecast,
    title="Monitoramento de Ressaca - Comparação",
    x_lim=True,
)

plt.show()
```

## Como Citar (Obrigatório)

Qualquer publicação científica, TCC, relatório, dashboard ou aplicação que utilize os dados fornecidos pela API deve citar a fonte e o DOI oficial:

**ABNT**
> NÚCLEO DE PESQUISAS HIDRODINÂMICAS (NPH-UNISANTA). NPH-Client & API da Sala de Situação da Baixada Santista: plataforma de dados hidro-meteoceanográficos (v1.0.0). Santos: Universidade Santa Cecília, 2026. Disponível em: https://doi.org/10.5281/zenodo.24142964.

**BibTeX**
```bibtex
@dataset{nph_unisanta_2026_ssbs,
  author       = {{NPH-UNISANTA}},
  title        = {{NPH-Client \& SS-BS API: Hydro-Meteoceanographic Data Platform for Baixada Santista}},
  year         = 2026,
  publisher    = {Zenodo},
  version      = {1.0.0},
  doi          = {10.5281/zenodo.24142964},
  url          = {[https://doi.org/10.5281/zenodo.24142964](https://doi.org/10.5281/zenodo.24142964)}
}
```

## Licença e Uso Comercial

- **Código-fonte (`nph-client`):** licenciado sob a [Licença MIT](LICENSE).
- **Dados fornecidos pela API:** licenciados sob [Creative Commons Atribuição-NãoComercial 4.0 Internacional (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).
- **Uso comercial:** estritamente proibido sem autorização prévia e formal por escrito da coordenação do NPH-UNISANTA. Para solicitações comerciais, entre em contato pelo e-mail **nph@unisanta.br**.