# Can AI Listen to the Market?

Monitoramento automatizado de notícias geração de um indicador/índice de mercado utilizando NLP e modelos de linguagem.

## Objetivo

Construir uma solução simples e modular capaz de:

1. Coletar notícias de diferentes portais financeiros.
2. Normalizar os dados em um formato comum.
3. Armazenar as notícias processadas.
4. Analisar relevância, sentimento e impacto esperado utilizando NLP/LLM.
5. Agregar os resultados em um indicador de tendência do mercado de energia.
6. Expor o indicador por meio de uma API.

O objetivo não é construir uma plataforma de produção, mas demonstrar a viabilidade e potencial técnico da solução.

---

## Arquitetura

```text
        News Sources
             │
     ┌───────┼───────┐
     │       │       │
     ▼       ▼       ▼
   RSS     RSS     RSS
     │       │       │
     └───────┼───────┘
             │
             ▼
         Collectors
             │
             ▼
       Normalization
             │
             ▼
      News Repository
            CSV
             │
             ▼
         NLP / LLM
      Microsoft Foundry
             │
             ▼
     Signal Aggregator
             │
             ▼
      Termômetro B3
             │
             ▼
           API
```



## Fontes de notícias

### MegaWhat

```text
https://megawhat.uol.com.br/feed/
```
### OUTRA (ADICIONAR)

---

## Output dos coletores

Todos os coletores devem produzir notícias utilizando a mesma estrutura lógica:

### Exeplo/sugestão:
```python
{
    "source": "...",
    "title": "...",
    "url": "...",
    "published_at": "...",
    "summary": "...",
    "content": "..."
}
```


---

Evitar commits diretamente na `main`.

---

## Etapas

### Etapa 1 — Coleta

Implementar o primeiro coletor:

```text
MegaWhat RSS
```

Responsabilidades:

* ler o RSS;
* identificar os campos disponíveis;
* converter cada notícia para o contrato comum;
* validar os resultados localmente.

### Etapa 2 — Normalização

Criar uma função comum para normalizar:

* source;
* title;
* URL;
* published_at;
* summary;
* content.

### Etapa 3 — Persistência

Salvar as notícias normalizadas inicialmente em CSV.

### Etapa 4 — NLP / LLM

Integrar Microsoft Foundry para avaliar:

* relevância para o mercado de energia;
* sentimento;
* impacto esperado;
* confiança da análise.

### Etapa 5 — Interpretador

Transformar os resultados individuais das notícias em um indicador agregado.

### Etapa 6 — API