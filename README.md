# Can AI Listen to the Market?

Monitoramento automatizado de notícias e geração de um indicador diário de sentimento de mercado utilizando **Python, NLP/LLM e Microsoft Foundry**.

O objetivo é demonstrar a possibilidade de transformar notícias de diferentes fontes em um sinal estruturado de mercado.

Além do indicador diário, o projeto inclui um experimento preditivo simples e
temporalmente correto: as informações disponíveis no dia `t` são usadas para
prever a direção do preço no próximo pregão. A comparação usa o mesmo modelo
com e sem a feature de notícias, evitando atribuir à IA uma melhora causada por
mudança de algoritmo.

---

## Arquitetura

```text
News Sources (RSS)
        │
        ▼
    Collectors
        │
        ▼
  Normalization
        │
        ▼
 News Repository
 CSV por categoria
        │
        ▼
     NLP / LLM
 Microsoft Foundry
   GPT-5.4-mini
        │
        ▼
 sentiment
 score
 relevance
 reason
        │
        ▼
 Signal Aggregator
        │
        ▼
 Daily Market Signal
     [-1, +1]
        ├──────────────► Streamlit Dashboard
        │
        ▼
  Notebooks de DS
 EDA + alinhamento temporal
        │
        ▼
 Direção do próximo pregão
   alta (1) / queda (0)
```

---

## Fluxo

### 1. Coleta

Cada fonte possui seu próprio collector em:

```text
src/collectors/
```

Os collectors acessam os feeds RSS e extraem as notícias disponíveis.

### 2. Normalização

Cada fonte possui seu normalizador em:

```text
src/normalization/
```

Independentemente da estrutura original do RSS, todas as notícias são convertidas para o contrato:

```python
{
    "source": "...",
    "title": "...",
    "summary": "...",
    "url": "...",
    "published_at": "...",
    "fetched_at": "..."
}
```

### 3. Persistência

As notícias normalizadas são armazenadas por categoria em:

```text
data/processed/
```

Exemplos:

```text
energy_br.csv
real_estate.csv
```

O repository também evita duplicação de notícias já coletadas.

### 4. NLP / LLM

As notícias ainda não analisadas são enviadas ao modelo **GPT-5.4-mini** via Microsoft Foundry.

Para cada notícia, o modelo retorna:

```json
{
    "sentiment": "positive | neutral | negative",
    "score": -1.0,
    "relevance": 0.0,
    "reason": "..."
}
```

Onde:

- `sentiment`: classificação do impacto;
- `score`: intensidade e direção do sentimento, entre -1 e +1;
- `relevance`: relevância da notícia para o mercado analisado, entre 0 e 1;
- `reason`: justificativa da classificação.

### 5. Signal Aggregator

O indicador é calculado diariamente utilizando a data de publicação das notícias.

```text
Σ(score × relevance)
────────────────────
    Σ(relevance)
```

Classificação utilizada na POC:

```text
signal < -0.15            NEGATIVE
-0.15 <= signal <= 0.15   NEUTRAL
signal > 0.15             POSITIVE
```

Os thresholds são heurísticos e não foram calibrados historicamente.

### 6. Dashboard

O dashboard Streamlit apresenta:

- sinal diário;
- histórico do indicador;
- quantidade de notícias analisadas;
- relevância média;
- distribuição de sentimento;
- feed das notícias;
- score, relevância e justificativa produzidos pelo LLM.

---

## Estrutura do projeto

```text
config/
└── sites/                 # Configuração das fontes

data/
├── processed/             # CSVs de notícias por categoria
├── market/                # Série diária de mercado
└── features/              # Bases produzidas pelos notebooks

notebooks/
├── 01_news_daily_features.ipynb       # Texto vira features numéricas
├── 02_market_news_eda.ipynb           # EDA, gráficos e alinhamento temporal
└── 03_next_day_direction_model.ipynb  # Classificação do próximo pregão

src/
├── collectors/            # Coleta RSS
├── normalization/         # Normalização por fonte
├── repository/            # Persistência e deduplicação
├── nlp/                   # Integração com LLM
├── signals/               # Cálculo do indicador
├── dashboard/             # Dashboard Streamlit
└── pipeline.py            # Orquestração do pipeline
```

---

## Configuração

O projeto utiliza [uv](https://docs.astral.sh/uv/) para gerenciamento do ambiente e dependências.

Clone o repositório:

```bash
git clone https://github.com/Hudson-Borgo/Can-AI-listen-to-the-market-.git
cd Can-AI-listen-to-the-market-
```

Instale as dependências:

```bash
uv sync
```

Crie o arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Configure no `.env` as credenciais necessárias para acesso ao Azure OpenAI / Microsoft Foundry.

---

## Executando o pipeline

Na raiz do projeto:

```bash
uv run python -m src.pipeline
```

O pipeline executa sequencialmente:

```text
Collect
   ↓
Normalize
   ↓
Persist / Deduplicate
   ↓
LLM Analysis
   ↓
Daily Market Signal
```

---

## Executando componentes isoladamente

Collector MegaWhat:

```bash
uv run python -m src.collectors.megawhat
```

NLP:

```bash
uv run python -m src.nlp.process_category
```

Signal Aggregator:

```bash
uv run python -m src.signals.aggregate
```

## Notebooks de Data Science

Execute os notebooks na ordem:

1. `01_news_daily_features.ipynb`: inspeciona e agrega as avaliações do LLM;
2. `02_market_news_eda.ipynb`: mostra scores, sinais e preço de fechamento,
   alinha fins de semana ao próximo pregão e gera a base de modelagem;
3. `03_next_day_direction_model.ipynb`: compara o mesmo classificador com e
   sem notícias usando validação temporal walk-forward.

O resultado principal é a acurácia média em quatro janelas futuras. Nesta POC,
o modelo base usa o retorno corrente; o modelo enriquecido adiciona
`negative_share`, a proporção diária de notícias classificadas pelo LLM como
negativas. O alvo é `direction_next_day`, derivado de `return_next_day > 0`.
Nenhuma informação do próximo pregão entra nas features.

> A série é curta. A melhora é uma evidência didática fora da amostra, não uma
> garantia de desempenho futuro nem uma estratégia de investimento.

---

## Executando o dashboard

Na raiz do projeto:

```bash
PYTHONPATH=. uv run streamlit run src/dashboard/app.py
```
```bash
$env:PYTHONPATH="."; uv run streamlit run src/dashboard/app.py
```

O Streamlit disponibilizará o dashboard localmente, normalmente em:

```text
http://localhost:8501
```

---
