
from pathlib import Path
import pandas as pd


NEWS_DIR = Path("data/processed")


# Salva noticias novas e evita registros duplicados.
def save_news(news: list[dict]) -> dict:
    """Salva as noticias normalizadas em um CSV por categoria."""

    received = len(news)

    # Retorna um resumo vazio quando nao ha noticias para salvar.
    if not news:
        return {
            "received": 0,
            "inserted": 0,
            "duplicates": 0,
            "total": 0,
        }

    categories = {item.get("category", "").strip() for item in news}
    if "" in categories:
        raise ValueError("Todas as noticias devem informar uma categoria.")

    primary_key = ["title", "url", "published_at"]
    inserted = 0
    total = 0

    # Cada categoria tem seu proprio conjunto de duplicatas e arquivo de destino.
    for category in categories:
        category_news = [item for item in news if item["category"].strip() == category]
        new_df = pd.DataFrame(category_news)
        news_path = NEWS_DIR / f"{category}.csv"

        if news_path.exists():
            current_df = pd.read_csv(news_path)
            existing_keys = set(
                current_df[primary_key].fillna("").itertuples(index=False, name=None)
            )
            mask = new_df[primary_key].fillna("").apply(
                lambda row: tuple(row) not in existing_keys, axis=1
            )
            new_df = new_df[mask]
            final_df = pd.concat([current_df, new_df], ignore_index=True)
        else:
            final_df = new_df

        inserted += len(new_df)
        total += len(final_df)
        NEWS_DIR.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(news_path, index=False)

    # Retorna os numeros para o pipeline exibir no terminal.
    return {
        "received": received,
        "inserted": inserted,
        "duplicates": received - inserted,
        "total": total,
    }