
from pathlib import Path
import pandas as pd



NEWS_PATH = Path("data/processed/news.csv")


# Salva noticias novas e evita registros duplicados.
def save_news(news: list[dict]) -> dict:
    """Salva as noticias normalizadas no arquivo CSV."""

    received = len(news)

    # Retorna um resumo vazio quando nao ha noticias para salvar.
    if not news:
        return {
            "received": 0,
            "inserted": 0,
            "duplicates": 0,
            "total": 0,
        }

  
    new_df = pd.DataFrame(news)

    PK = ["title", "url", "published_at"]

    # Verifica se ja existe um repositorio salvo.
    if NEWS_PATH.exists():
        current_df = pd.read_csv(NEWS_PATH)

        # Composite key as a frozenset of tuples to handle missing columns gracefully.
        existing_keys = set(
            current_df[PK].fillna("").itertuples(index=False, name=None)
        )

        mask = new_df[PK].fillna("").apply(
            lambda row: tuple(row) not in existing_keys, axis=1
        )
        new_df = new_df[mask]

        inserted = len(new_df)

        final_df = pd.concat(
            [current_df, new_df],
            ignore_index=True,
        )

    else:
        # Quando o arquivo nao existe, todas as noticias sao novas.
        inserted = len(new_df)
        final_df = new_df

    # Cria a pasta de destino caso ela ainda nao exista.
    NEWS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Salva a tabela completa no arquivo CSV.
    final_df.to_csv(
        NEWS_PATH,
        index=False,
    )

    # Retorna os numeros para o pipeline exibir no terminal.
    return {
        "received": received,
        "inserted": inserted,
        "duplicates": received - inserted,
        "total": len(final_df),
    }