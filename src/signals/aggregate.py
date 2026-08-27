from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/processed")


def classify_signal(signal: float) -> str:
    """
    Converte o sinal numerico em uma classificacao de tendencia.

    Os thresholds sao heuristicas definidas para:
    abaixo de -0.15  -> NEGATIVE
    entre -0.15 e 0.15 -> NEUTRAL
    acima de 0.15 -> POSITIVE
    """

    if signal > 0.15:
        return "POSITIVE"

    if signal < -0.15:
        return "NEGATIVE"

    return "NEUTRAL"


def calculate_daily_signals(category: str) -> pd.DataFrame:
    """
    Calcula o sinal diario de mercado para uma categoria.

    Formula:

        signal =
            sum(score * relevance)
            ----------------------
               sum(relevance)

    Apenas noticias que ja passaram pela analise do LLM
    sao consideradas.

    A data de referencia e published_at, ou seja,
    o dia em que a noticia foi publicada.
    """

    csv_path = DATA_PATH / f"{category}.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {csv_path}"
        )

    df = pd.read_csv(csv_path)

    # ---------------------------------------------------------
    # Considera apenas noticias analisadas pelo LLM
    # ---------------------------------------------------------

    analyzed = df.dropna(
        subset=[
            "published_at",
            "score",
            "relevance",
        ]
    ).copy()

    if analyzed.empty:
        raise ValueError(
            f"No analyzed articles found for category: {category}"
        )

    # ---------------------------------------------------------
    # Converte published_at para datetime
    # ---------------------------------------------------------

    analyzed["published_at"] = pd.to_datetime(
        analyzed["published_at"],
        utc=True,
    )

    # ---------------------------------------------------------
    # Extrai apenas o dia da publicacao
    #
    # Exemplo:
    # 2026-08-19T15:30:13+00:00
    #              ↓
    # 2026-08-19
    # ---------------------------------------------------------

    analyzed["date"] = (
        analyzed["published_at"]
        .dt.date
    )

    # ---------------------------------------------------------
    # Calcula a contribuicao de cada noticia
    #
    # score × relevance
    # ---------------------------------------------------------

    analyzed["weighted_score"] = (
        analyzed["score"]
        * analyzed["relevance"]
    )

    # ---------------------------------------------------------
    # Agrupa todas as noticias pelo dia de publicacao
    # ---------------------------------------------------------

    daily = (
        analyzed
        .groupby("date")
        .agg(
            articles=("score", "count"),
            weighted_sum=("weighted_score", "sum"),
            total_relevance=("relevance", "sum"),
            average_relevance=("relevance", "mean"),
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # Calcula o sinal diario
    #
    # sum(score × relevance)
    # ----------------------
    #    sum(relevance)
    # ---------------------------------------------------------

    daily["signal"] = (
        daily["weighted_sum"]
        / daily["total_relevance"]
    )

    # ---------------------------------------------------------
    # Converte o valor numerico para uma tendencia
    # ---------------------------------------------------------

    daily["trend"] = (
        daily["signal"]
        .apply(classify_signal)
    )

    # ---------------------------------------------------------
    # Arredonda apenas para apresentacao
    # ---------------------------------------------------------

    daily["signal"] = daily["signal"].round(3)

    daily["average_relevance"] = (
        daily["average_relevance"]
        .round(3)
    )

    # ---------------------------------------------------------
    # Mantemos apenas as informacoes que interessam
    # para o indicador
    # ---------------------------------------------------------

    return daily[
        [
            "date",
            "articles",
            "average_relevance",
            "signal",
            "trend",
        ]
    ]


def main():
    category = "energy_br"

    print("\n" + "=" * 70)
    print("  ENERGY MARKET SIGNAL")
    print("=" * 70)

    # Calcula toda a serie historica disponivel.
    daily_signals = calculate_daily_signals(category)

    # ---------------------------------------------------------
    # SERIES HISTORY
    # ---------------------------------------------------------

    print("\n  DAILY SIGNAL HISTORY")
    print("-" * 70)

    print(
        daily_signals.to_string(
            index=False
        )
    )

    # ---------------------------------------------------------
    # CURRENT SIGNAL
    #
    # O ultimo dia disponivel no dataset representa
    # o sinal mais recente do mercado.
    # ---------------------------------------------------------

    current = daily_signals.iloc[-1]

    print("\n" + "=" * 70)
    print("  CURRENT MARKET SIGNAL")
    print("=" * 70)

    print(f"\n  Category          : {category}")
    print(f"  Reference date    : {current['date']}")
    print(f"  Articles analyzed : {current['articles']}")
    print(
        f"  Average relevance : "
        f"{current['average_relevance']:.3f}"
    )

    print("\n  Weighted formula:")
    print("  Σ(score × relevance) / Σ(relevance)")

    print(
        f"\n  MARKET SIGNAL     : "
        f"{current['signal']:+.3f}"
    )

    print(
        f"  MARKET TREND      : "
        f"{current['trend']}"
    )

    print("\n" + "-" * 70)
    print("  -1.0              0.0              +1.0")
    print("  NEGATIVE        NEUTRAL          POSITIVE")
    print("-" * 70)

    print("\n  ✓ DAILY MARKET SIGNAL CALCULATED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()