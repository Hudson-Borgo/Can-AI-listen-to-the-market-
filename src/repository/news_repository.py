
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

    # Verifica se ja existe um repositorio salvo.
    if NEWS_PATH.exists():
        # Carrega as noticias que ja foram salvas.
        current_df = pd.read_csv(NEWS_PATH)

        # Guarda os links existentes para identificar duplicatas.
        existing_urls = set(current_df["url"].dropna())

        # Mantem apenas noticias com links ainda nao registrados.
        new_df = new_df[
            ~new_df["url"].isin(existing_urls)
        ]

        # Junta as noticias antigas com as novas.
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