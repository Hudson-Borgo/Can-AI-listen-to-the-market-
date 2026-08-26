from pathlib import Path

import pandas as pd

from src.nlp.analyze import analyze_news
from src.nlp.prompts.energy_br import SYSTEM_PROMPT


DATA_PATH = Path("data/processed")


def process_category(
    category: str,
    show_header: bool = True,
) -> None:

    csv_path = DATA_PATH / f"{category}.csv"

    if show_header:
        print("\n" + "=" * 70)
        print("  AI MARKET ANALYSIS")
        print("=" * 70)

    print(f"\nCategory : {category}")
    print(f"Dataset  : {csv_path}")

    if not csv_path.exists():
        print("\n✗ Dataset not found.")
        return

    df = pd.read_csv(csv_path)

    print(f"Articles : {len(df)}")

    # Cria as colunas de NLP caso ainda nao existam.
    nlp_columns = [
        "sentiment",
        "score",
        "relevance",
        "reason",
    ]

    for column in nlp_columns:
        if column not in df.columns:
            df[column] = None

    # Apenas noticias ainda nao processadas.
    pending = df["sentiment"].isna()

    pending_count = int(pending.sum())

    print(f"Pending  : {pending_count}")

    if pending_count == 0:
        print("\n✓ All articles already analyzed.")
        return

    print("\nStarting AI analysis...\n")

    total = pending_count
    processed = 0
    errors = 0

    for current, index in enumerate(
        df[pending].index,
        start=1,
    ):
        title = df.at[index, "title"]
        summary = df.at[index, "summary"]

        print("-" * 70)
        print(f"[{current}/{total}] {title}")
        print("Sending to GPT-5.4-mini...")

        try:
            result = analyze_news(
                title=title,
                summary=summary,
                system_prompt=SYSTEM_PROMPT,
            )

            df.at[index, "sentiment"] = result["sentiment"]
            df.at[index, "score"] = result["score"]
            df.at[index, "relevance"] = result["relevance"]
            df.at[index, "reason"] = result["reason"]

            # Checkpoint:
            # salva imediatamente apos cada analise concluida.
            df.to_csv(
                csv_path,
                index=False,
            )

            processed += 1

            print(
                f"Result    : "
                f"{result['sentiment'].upper()} "
                f"({result['score']})"
            )

            print(
                f"Relevance : "
                f"{result['relevance']}"
            )

            print(
                f"Reason    : "
                f"{result['reason']}"
            )

            print("Saved     : ✓")

        except Exception as error:
            errors += 1
            print(f"✗ Error: {error}")

    print("\n" + "=" * 70)
    print("  ✓ AI ANALYSIS COMPLETED")
    print(f"  Processed : {processed}")
    print(f"  Errors    : {errors}")
    print(f"  Remaining : {total - processed}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    process_category("energy_br")