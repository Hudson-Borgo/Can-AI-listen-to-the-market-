
from src.collectors.megawhat import collect_news
from src.normalization.megawhat import normalize_news
from src.repository.news_repository import save_news



def main():
    """Executa o pipeline completo de coleta, normalizacao e salvamento de noticias."""
    print("\n" + "=" * 70)
    print("  CAN AI LISTEN TO THE MARKET?")
    print("  Energy Market Intelligence Pipeline")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. COLLECTION
    # ---------------------------------------------------------

    print("\n[1/3] COLLECTING NEWS")
    print("      Source: MegaWhat")
    print("      Method: RSS")

    # Busca as noticias no feed RSS.
    raw_news = collect_news()

    print(f"      ✓ {len(raw_news)} news articles collected")

    # ---------------------------------------------------------
    # 2. NORMALIZATION
    # ---------------------------------------------------------

    print("\n[2/3] NORMALIZING DATA")

    # Padroniza os dados recebidos antes de salvar.
    normalized_news = [
        normalize_news(item)
        for item in raw_news
    ]

    print(f"      ✓ {len(normalized_news)} articles normalized")

    # Mostra uma noticia de exemplo quando houver dados.
    if normalized_news:
        example = normalized_news[0]

        print("\n      Example:")
        print(f"      Title: {example['title']}")
        print(f"      Published: {example['published_at']}")

    # ---------------------------------------------------------
    # 3. REPOSITORY
    # ---------------------------------------------------------

    print("\n[3/3] UPDATING NEWS REPOSITORY")

    # Salva as noticias e recebe um resumo da operacao.
    result = save_news(normalized_news)

    print(f"      Received : {result['received']}")
    print(f"      New      : {result['inserted']}")
    print(f"      Duplicates: {result['duplicates']}")
    print(f"      Total    : {result['total']}")

    print("\n" + "=" * 70)
    print("  ✓ PIPELINE COMPLETED")
    print("=" * 70 + "\n")


# Permite executar o pipeline diretamente pelo terminal.
if __name__ == "__main__":
    main()