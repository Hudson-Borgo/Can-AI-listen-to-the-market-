from src.collectors.megawhat import collect_news as collect_megawhat
from src.collectors.idealista import collect_news as collect_idealista
from src.collectors.eco import collect_news as collect_eco
from src.collectors.jornaldenegocios import collect_news as collect_jornaldenegocios

from src.normalization.megawhat import normalize_news as normalize_megawhat
from src.normalization.idealista import normalize_news as normalize_idealista
from src.normalization.eco import normalize_news as normalize_eco
from src.normalization.jornaldenegocios import normalize_news as normalize_jornaldenegocios

from src.repository.news_repository import save_news
from src.signals.aggregate import calculate_daily_signals
# Responsavel por ler o CSV da categoria e enviar apenas as noticias
# ainda nao analisadas para o modelo no Azure OpenAI / Foundry.
from src.nlp.process_category import process_category


def main():
    """
    Executa o pipeline completo:
    coleta -> normalizacao -> repositorio -> analise com LLM.
    """

    print("\n" + "=" * 70)
    print("  CAN AI LISTEN TO THE MARKET?")
    print("  Market Intelligence Pipeline")
    print("=" * 70)

    # =========================================================
    # 1. COLLECTION — MegaWhat
    # =========================================================
    # Chama:
    # src/collectors/megawhat.py
    #
    # Responsabilidade:
    # Ler o RSS do MegaWhat e retornar as noticias no formato
    # bruto fornecido pela fonte.
    # =========================================================

    print("\n[1/7] COLLECTING NEWS")
    print("      Source   : MegaWhat")
    print("      Category : energy_br")
    print("      Method   : RSS")

    raw_megawhat = collect_megawhat()

    print(f"      ✓ {len(raw_megawhat)} news articles collected")

    # =========================================================
    # 2. COLLECTION — Idealista
    # =========================================================
    # Chama:
    # src/collectors/idealista.py
    #
    # Responsabilidade:
    # Ler o RSS do Idealista e retornar as noticias brutas.
    # =========================================================

    print("\n[2/7] COLLECTING NEWS")
    print("      Source   : Idealista")
    print("      Category : real_estate")
    print("      Method   : RSS")

    raw_idealista = collect_idealista()

    print(f"      ✓ {len(raw_idealista)} news articles collected")

    # =========================================================
    # 3. COLLECTION — ECO
    # =========================================================
    # Chama:
    # src/collectors/eco.py
    #
    # Responsabilidade:
    # Ler o RSS do ECO e retornar as noticias brutas.
    # =========================================================

    print("\n[3/7] COLLECTING NEWS")
    print("      Source   : ECO")
    print("      Method   : RSS")

    raw_eco = collect_eco()

    print(f"      ✓ {len(raw_eco)} news articles collected")

    # =========================================================
    # 4. COLLECTION — Jornal de Negocios
    # =========================================================
    # Chama:
    # src/collectors/jornaldenegocios.py
    #
    # Responsabilidade:
    # Ler o RSS do Jornal de Negocios e retornar as noticias
    # brutas.
    # =========================================================

    print("\n[4/7] COLLECTING NEWS")
    print("      Source   : Jornal de Negocios")
    print("      Method   : RSS")

    raw_jornaldenegocios = collect_jornaldenegocios()

    print(f"      ✓ {len(raw_jornaldenegocios)} news articles collected")

    # =========================================================
    # 5. NORMALIZATION
    # =========================================================
    # Chama os normalizadores especificos de cada fonte:
    #
    # src/normalization/megawhat.py
    # src/normalization/idealista.py
    # src/normalization/eco.py
    # src/normalization/jornaldenegocios.py
    #
    # Responsabilidade:
    # Converter as particularidades de cada RSS para o nosso
    # contrato comum:
    #
    # {
    #     "source": ...,
    #     "title": ...,
    #     "summary": ...,
    #     "url": ...,
    #     "published_at": ...,
    #     "fetched_at": ...
    # }
    # =========================================================

    print("\n[5/7] NORMALIZING DATA")

    normalized_news = (
        [normalize_megawhat(item) for item in raw_megawhat]
        + [normalize_idealista(item) for item in raw_idealista]
        + [normalize_eco(item) for item in raw_eco]
        + [
            normalize_jornaldenegocios(item)
            for item in raw_jornaldenegocios
        ]
    )

    print(f"      ✓ {len(normalized_news)} articles normalized")

    if normalized_news:
        example = normalized_news[0]

        print("\n      Normalized example:")
        print(f"      Source    : {example['source']}")
        print(f"      Title     : {example['title']}")
        print(f"      Published : {example['published_at']}")

    # =========================================================
    # 6. NEWS REPOSITORY
    # =========================================================
    # Chama:
    # src/repository/news_repository.py
    #
    # Responsabilidade:
    # - separar as noticias por categoria;
    # - atualizar o CSV correspondente;
    # - evitar duplicacoes;
    #
    # Exemplos:
    #
    # data/processed/energy_br.csv
    # data/processed/real_estate.csv
    # =========================================================

    print("\n[6/7] UPDATING NEWS REPOSITORY")

    result = save_news(normalized_news)

    print(f"      Received   : {result['received']}")
    print(f"      New        : {result['inserted']}")
    print(f"      Duplicates : {result['duplicates']}")
    print(f"      Total      : {result['total']}")

    # =========================================================
    # 7. NLP / LLM — ENERGY BR
    # =========================================================
    # Chama:
    # src/nlp/process_category.py
    #
    # Esse modulo, por sua vez, chama:
    # src/nlp/analyze.py
    #       ↓
    # src/nlp/client.py
    #       ↓
    # Azure OpenAI / Microsoft Foundry
    #       ↓
    # GPT-5.4-mini
    #
    # O prompt utilizado para esta categoria esta em:
    # src/nlp/prompts/energy_br.py
    #
    # Responsabilidade:
    # Ler data/processed/energy_br.csv, identificar noticias
    # ainda nao analisadas e gerar:
    #
    # {
    #     "sentiment": ...,
    #     "score": ...,
    #     "relevance": ...,
    #     "reason": ...
    # }
    #
    # Neste momento executamos NLP apenas para energy_br.
    # As outras categorias poderao reutilizar o mesmo mecanismo,
    # trocando principalmente o prompt da categoria.
    # =========================================================

    print("\n[7/7] ANALYZING MARKET IMPACT")
    print("      Category : energy_br")
    print("      Model    : GPT-5.4-mini")
    print("      Platform : Microsoft Foundry")

    process_category(
        "energy_br",
        show_header=False,
    )

    # =========================================================
    # 8. DAILY MARKET SIGNAL
    # =========================================================
    # Chama:
    # src/signals/aggregate.py
    #
    # Responsabilidade:
    # - ler as noticias ja analisadas pelo LLM;
    # - agrupar as noticias por published_at;
    # - ponderar o score pela relevancia;
    # - calcular o sinal diario entre -1 e +1;
    # - classificar a tendencia como:
    #   NEGATIVE, NEUTRAL ou POSITIVE.
    #
    # Formula:
    #
    #   Σ(score × relevance)
    #   --------------------
    #       Σ(relevance)
    #
    # O ultimo dia disponivel representa o sinal
    # mais recente do mercado.
    # =========================================================

    print("\n[8/8] CALCULATING DAILY MARKET SIGNAL")

    daily_signals = calculate_daily_signals("energy_br")

    current = daily_signals.iloc[-1]

    print(f"      Category          : energy_br")
    print(f"      Reference date    : {current['date']}")
    print(f"      Articles analyzed : {current['articles']}")
    print(
        f"      Average relevance : "
        f"{current['average_relevance']:.3f}"
    )

    print("\n      Weighted formula:")
    print("      Σ(score × relevance) / Σ(relevance)")

    print(
        f"\n      MARKET SIGNAL     : "
        f"{current['signal']:+.3f}"
    )

    print(
        f"      MARKET TREND      : "
        f"{current['trend']}"
    )

    ########################

    print("\n      " + "-" * 54)
    print("      -1.0              0.0              +1.0")
    print("      NEGATIVE        NEUTRAL          POSITIVE")
    print("      " + "-" * 54)





    # =========================================================
    # PIPELINE FINISHED
    # =========================================================

    print("\n" + "=" * 70)
    print("  ✓ PIPELINE COMPLETED")
    print("=" * 70 + "\n")


# Permite executar todo o pipeline diretamente pelo terminal:
#
# uv run python -m src.pipeline
#
if __name__ == "__main__":
    main()