from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
import sys

import pandas as pd

# Force UTF-8 on Windows where the default terminal encoding (cp1252) breaks
# non-ASCII characters in the LLM output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.nlp.analyze import analyze_news
from src.nlp.client import get_client
from src.nlp.prompts.energy_br import SYSTEM_PROMPT


DATA_PATH = Path("data/processed")
CHECKPOINT_EVERY = 10


def process_category(
    category: str,
    show_header: bool = True,
    workers: int = 10,
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
        "classified_at",
    ]

    for column in nlp_columns:
        if column not in df.columns:
            df[column] = None

    # Columns read from an all-NaN CSV are inferred as float64; cast to object
    # so string assignments (e.g. "positive") are accepted without TypeError.
    df[nlp_columns] = df[nlp_columns].astype(object)

    # Apenas noticias ainda nao processadas.
    pending = df["sentiment"].isna()

    pending_count = int(pending.sum())

    print(f"Pending  : {pending_count}")

    if pending_count == 0:
        print("\n✓ All articles already analyzed.")
        return

    print(f"\nStarting AI analysis (workers={workers})...\n")

    total = pending_count
    processed = 0
    errors = 0

    # Each thread gets its own client to avoid connection pool contention.
    csv_lock = Lock()

    def _analyze(index: int) -> tuple[int, dict | Exception]:
        thread_client = get_client()
        title = df.at[index, "title"]
        summary = df.at[index, "summary"]
        try:
            result = analyze_news(
                title=title,
                summary=summary,
                system_prompt=SYSTEM_PROMPT,
                client=thread_client,
            )
            return index, result
        except Exception as exc:
            return index, exc

    pending_indices = list(df[pending].index)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_analyze, idx): idx
            for idx in pending_indices
        }

        completed_since_checkpoint = 0

        for future in as_completed(futures):
            try:
                index, outcome = future.result()
                title = df.at[index, "title"]

                print("-" * 70)
                print(f"[{processed + errors + 1}/{total}] {title}")

                if isinstance(outcome, Exception):
                    errors += 1
                    print(f"✗ Error: {outcome}")
                else:
                    df.at[index, "sentiment"] = outcome["sentiment"]
                    df.at[index, "score"] = outcome["score"]
                    df.at[index, "relevance"] = outcome["relevance"]
                    df.at[index, "reason"] = outcome["reason"]
                    df.at[index, "classified_at"] = datetime.now(timezone.utc).isoformat()

                    processed += 1
                    completed_since_checkpoint += 1

                    print(
                        f"Result    : "
                        f"{outcome['sentiment'].upper()} "
                        f"({outcome['score']})"
                    )
                    print(f"Relevance : {outcome['relevance']}")
                    print(f"Reason    : {outcome['reason']}")

                    # Checkpoint: periodic save to preserve progress on crashes.
                    if completed_since_checkpoint >= CHECKPOINT_EVERY:
                        with csv_lock:
                            df.to_csv(csv_path, index=False)
                        completed_since_checkpoint = 0
                        print("Checkpoint: ✓")

            except Exception as loop_exc:
                errors += 1
                print(f"✗ Unexpected error: {type(loop_exc).__name__}: {loop_exc}")

    # Final save.
    df.to_csv(csv_path, index=False)

    print("\n" + "=" * 70)
    print("  ✓ AI ANALYSIS COMPLETED")
    print(f"  Processed : {processed}")
    print(f"  Errors    : {errors}")
    print(f"  Remaining : {total - processed}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    process_category("energy_br")