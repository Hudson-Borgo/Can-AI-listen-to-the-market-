from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/processed/energy_br.csv")


def load_energy_news() -> pd.DataFrame:
    """
    Carrega o dataset de noticias de energia ja processado pelo pipeline.
    """

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    # Converte as colunas numericas produzidas pelo LLM.
    df["score"] = pd.to_numeric(
        df["score"],
        errors="coerce",
    )

    df["relevance"] = pd.to_numeric(
        df["relevance"],
        errors="coerce",
    )

    # Converte a data de publicacao.
    df["published_at"] = pd.to_datetime(
        df["published_at"],
        utc=True,
        errors="coerce",
    )

    return df