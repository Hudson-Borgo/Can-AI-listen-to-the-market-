
from src.collectors.megawhat import collect_news as collect_megawhat
from src.collectors.idealista import collect_news as collect_idealista
from src.collectors.eco import collect_news as collect_eco
from src.collectors.jornaldenegocios import collect_news as collect_jornaldenegocios
from src.normalization.megawhat import normalize_news as normalize_megawhat
from src.normalization.idealista import normalize_news as normalize_idealista
from src.normalization.eco import normalize_news as normalize_eco
from src.normalization.jornaldenegocios import normalize_news as normalize_jornaldenegocios
from src.repository.news_repository import save_news



def main():
    """Executa o pipeline completo de coleta, normalizacao e salvamento de noticias."""
    print("\n" + "=" * 70)
    print("  CAN AI LISTEN TO THE MARKET?")
    print("  Energy Market Intelligence Pipeline")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. COLLECTION — MegaWhat
    # ---------------------------------------------------------

    print("\n[1/6] COLLECTING NEWS")
    print("      Source: MegaWhat")
    print("      Method: RSS")

    raw_megawhat = collect_megawhat()

    print(f"      ✓ {len(raw_megawhat)} news articles collected")

    # ---------------------------------------------------------
    # 2. COLLECTION — Idealista
    # ---------------------------------------------------------

    print("\n[2/6] COLLECTING NEWS")
    print("      Source: Idealista")
    print("      Method: RSS")

    raw_idealista = collect_idealista()

    print(f"      ✓ {len(raw_idealista)} news articles collected")

    # ---------------------------------------------------------
    # 3. COLLECTION — ECO
    # ---------------------------------------------------------

    print("\n[3/6] COLLECTING NEWS")
    print("      Source: ECO")
    print("      Method: RSS")

    raw_eco = collect_eco()

    print(f"      ✓ {len(raw_eco)} news articles collected")

    # ---------------------------------------------------------
    # 4. COLLECTION — Jornal de Negócios
    # ---------------------------------------------------------

    print("\n[4/6] COLLECTING NEWS")
    print("      Source: Jornal de Negócios")
    print("      Method: RSS")

    raw_jornaldenegocios = collect_jornaldenegocios()

    print(f"      ✓ {len(raw_jornaldenegocios)} news articles collected")

    # ---------------------------------------------------------
    # 5. NORMALIZATION
    # ---------------------------------------------------------

    print("\n[5/6] NORMALIZING DATA")

    normalized_news = (
        [normalize_megawhat(item) for item in raw_megawhat]
        + [normalize_idealista(item) for item in raw_idealista]
        + [normalize_eco(item) for item in raw_eco]
        + [normalize_jornaldenegocios(item) for item in raw_jornaldenegocios]
    )

    print(f"      ✓ {len(normalized_news)} articles normalized")

    if normalized_news:
        example = normalized_news[0]

        print("\n      Example:")
        print(f"      Title: {example['title']}")
        print(f"      Published: {example['published_at']}")

    # ---------------------------------------------------------
    # 6. REPOSITORY
    # ---------------------------------------------------------

    print("\n[6/6] UPDATING NEWS REPOSITORY")

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