# Can AI Listen to the Market?

Monitoramento automatizado de notícias e geração de um indicador diário de sentimento de mercado utilizando **Python, NLP/LLM e Microsoft Foundry**.

O objetivo é demonstrar a possibilidade de transformar notícias de diferentes fontes em um sinal estruturado de mercado.

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
        │
        ▼
 Streamlit Dashboard
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
└── processed/             # CSVs por categoria

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

---

## Executando o dashboard

Na raiz do projeto:

```bash
PYTHONPATH=. uv run streamlit run src/dashboard/app.py
```

O Streamlit disponibilizará o dashboard localmente, normalmente em:

```text
http://localhost:8501
```

---

## Análise de Visualização: Price + News Overlay

O script `scripts/price_news_overlay.py` gera um gráfico interativo em HTML que sobrepõe o preço de mercado M1 com os eventos de notícias classificados pelo LLM.

```bash
python scripts/price_news_overlay.py
# output: data/processed/price_news_overlay.html
```

O ficheiro HTML é auto-contido e pode ser aberto em qualquer browser (requer acesso à internet para carregar o plotly.js via CDN).

### Elementos do gráfico

#### Painel principal — Preço + Notícias

| Elemento | Descrição |
|---|---|
| **Banda cinzenta** | Intervalo diário de preço: `preco_min` a `preco_max` |
| **Linha escura** | `preco_fecho` — preço de fecho (eixo esquerdo, €/MWh) |
| **▲ marcador verde** | Evento de notícia com `score ≥ +0.75`, posicionado no preço de fecho da data de publicação |
| **▼ marcador vermelho** | Evento de notícia com `score ≤ −0.75`, posicionado da mesma forma |
| **Rectângulos verdes/vermelhos** | Janela de impacto de 1 mês a partir da data do evento; a opacidade é calculada por evento como `\|score\| × relevance × 0.18` — mais intenso significa maior convicção, não maior quantidade de eventos |
| **Linha roxa pontilhada** | Média móvel ponderada por relevância dos últimos 14 dias (eixo direito, −1 a +1) — ver fórmula abaixo |

#### Painel inferior — Event rug

Um traço vertical por evento de alta convicção (`|score| ≥ 0.75`), colorido a verde (positivo) ou vermelho (negativo). Permite identificar visualmente clusters e períodos de baixa densidade de sinal.

#### Interatividade

- **Hover num marcador ▲/▼**: mostra o título da notícia, score, fonte e data de publicação.
- **Hover na linha de preço**: mostra a data e o preço de fecho.
- **Hover na linha roxa**: mostra a data e o valor da média móvel.
- Clicar num item da legenda activa/desactiva esse elemento.

### Fórmula da média móvel ponderada

Apenas notícias com `|score| > 0.3` são consideradas. Para cada janela de 14 dias até ao dia `t`:

```
rolling_score(t) = Σ( score_i × relevance_i ) / Σ( relevance_i )
```

Onde o somatório percorre todos os artigos publicados nos 14 dias anteriores a `t` com `|score| > 0.3`. Dias sem notícias elegíveis não contribuem com zero — são simplesmente ausentes da série.

### Parâmetros configuráveis (topo do script)

| Constante | Valor padrão | Significado |
|---|---|---|
| `SCORE_THRESHOLD` | `0.75` | Limiar para marcadores e janelas de impacto |
| `ROLL_THRESHOLD` | `0.3` | Limiar mínimo de `\|score\|` para a média móvel |
| `ROLL_WINDOW` | `"14D"` | Janela temporal da média móvel |
| `MAX_BAND_OPACITY` | `0.18` | Opacidade máxima das janelas de impacto |

---