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

- **Documentação on-line:** https://nph.unisanta.br/ssbs/pt
- **Novo cadastro e solicitação de chave (`apiKey`):** https://nph.unisanta.br/ssbs/request
- **Login e dashboard da plataforma:** https://nph.unisanta.br/ssbs

Você pode passar a chave diretamente ao inicializar `NPHClient(api_key)` ou configurá-la na variável de ambiente `NPH_API_KEY` (recomendado para não expor credenciais em scripts e notebooks).

## Uso Rápido (Exemplo: Pluviômetro Cota-200, Cubatão — ID 310)

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
    stations=[310],  # Cota-200 (Cubatão)
    start_date="2026-01-01",
    end_date="2026-01-03",
    return_value=0,
    time_offset=timedelta(hours=-3),
)
```

### 3. Consultar previsões de modelos numéricos

```python
df_forecasts = client.get_forecasts(
    stations=[310],       # Cota-200 (Cubatão)
    model_id="WRF 3km",   # ou 1 (ver Glossário; distinto do ID centralizador de /sources)
    param_id="Precipitação",  # ou 2
    start_date="2026-01-01",
    end_date="2026-01-03",
    time_offset=timedelta(hours=-3),
)
```

### 4. Gerar gráficos com limiares (`plotter`)

```python
import matplotlib.pyplot as plt
from nph_client.plotting import AxisConfig, Threshold, plot_series

limiar_atencao = Threshold(
    value=10.0,
    color="orange",
    label="ATENÇÃO (10 mm/h)",
    fill_above=True,
    max_fill_value=25.0,
    alpha=0.15,
)

limiar_alerta = Threshold(
    value=25.0,
    color="red",
    label="ALERTA (25 mm/h)",
    fill_above=True,
    alpha=0.18,
)

conf_measurement = AxisConfig(
    plot_type="bar",
    label="Precipitação Medida (mm)",
    columns=list(df_measurements.columns),
    min_val=0.0,
    max_val=50.0,
    step=10.0,
    thresholds=[limiar_atencao, limiar_alerta],
    plot_kwargs={"alpha": 0.75, "color": "#1f77b4"},
)

conf_forecast = AxisConfig(
    plot_type="line",
    label="Previsão WRF 3km (mm)",
    columns=list(df_forecasts.columns),
    min_val=0.0,
    max_val=50.0,
    step=10.0,
    plot_kwargs={"alpha": 1.0, "linewidth": 2.0, "color": "#0b3a5b"},
)

plot_series(
    df=[df_measurements, df_forecasts],
    primary_conf=conf_measurement,
    secondary_conf=conf_forecast,
    title="Precipitação - Cota-200 (Cubatão) - Medido vs WRF 3km",
    x_lim=True,
)

plt.show()
```

## Como Citar (Obrigatório)

Qualquer publicação científica, TCC, relatório, dashboard ou aplicação que utilize os dados fornecidos pela API deve citar a plataforma, o DOI oficial e as fontes originais dos dados:

**ABNT**
> NUSCH, G. S.; RUIZ, M. S.; FERREIRA, R. S.; RIBEIRO, R. B.; GOMES, K. L.; LIMA, M. M. S.; BEZERRA, V. L. V.; SAMPAIO, A. F. P. **NPH-Client: API e pacote Python para dados hidro-meteoceanográficos da Baixada Santista**. Versão 1.0.1. Santos: Núcleo de Pesquisas Hidrodinâmicas da Universidade Santa Cecília (NPH-UNISANTA), 2026. DOI: 10.5281/zenodo.24142964. Disponível em: https://nph.unisanta.br/ssbs/pt.

**APA**
> Nusch, G. S., Ruiz, M. S., Ferreira, R. S., Ribeiro, R. B., Gomes, K. L., Lima, M. M. S., Bezerra, V. L. V., & Sampaio, A. F. P. (2026). *NPH-Client: API e pacote Python para dados hidro-meteoceanográficos da Baixada Santista* (Versão 1.0.1) [Software]. Núcleo de Pesquisas Hidrodinâmicas da Universidade Santa Cecília (NPH-UNISANTA). https://doi.org/10.5281/zenodo.24142964

**BibTeX**
```bibtex
@software{nusch_2026_nph_client,
  author       = {Nusch, Gustavo Silva and
                  Ruiz, Matheus Souza and
                  Ferreira, Regina de Souza and
                  Ribeiro, Renan Braga and
                  Gomes, Kauê Leocádio and
                  Lima, Mariana Marques Schermack de and
                  Bezerra, Valentina Luize Vidal and
                  Sampaio, Alexandra Franciscatto Penteado},
  title        = {{NPH-Client: API e pacote Python para dados hidro-meteoceanográficos da Baixada Santista}},
  year         = 2026,
  publisher    = {Zenodo},
  version      = {1.0.1},
  doi          = {10.5281/zenodo.24142964},
  url          = {[https://doi.org/10.5281/zenodo.24142964](https://doi.org/10.5281/zenodo.24142964)}
}
```

## Licença e Uso Comercial

- **Código-fonte (`nph-client`):** licenciado sob a [Licença MIT](LICENSE).
- **Dados fornecidos pela API:** licenciados sob [Creative Commons Atribuição-NãoComercial 4.0 Internacional (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).
- **Uso comercial:** estritamente proibido sem autorização prévia e formal por escrito da coordenação do NPH-UNISANTA. Para solicitações comerciais, entre em contato pelo e-mail **nph@unisanta.br**.