"""
Build daily min/max score time series from a processed NLP CSV.

Usage:
    python scripts/score_timeseries.py
    python scripts/score_timeseries.py data/processed/energy_br.csv
"""

import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_INPUT = Path("data/processed/energy_br.csv")
OUTPUT_CSV = Path("data/processed/score_timeseries.csv")
OUTPUT_PNG = Path("data/processed/score_timeseries.png")

COLOR_MIN = "#e74c3c"
COLOR_MAX = "#2ecc71"


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in ("published_at", "score") if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
    df["date"] = df["published_at"].dt.date
    return df.dropna(subset=["score"])


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    daily = (
        df.groupby("date")["score"]
        .agg(score_min="min", score_max="max")
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"])
    return daily.sort_values("date")


def save_csv(daily: pd.DataFrame, out: Path) -> None:
    daily.to_csv(out, index=False)
    print(f"CSV saved → {out}")


def plot(daily: pd.DataFrame, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(daily["date"], daily["score_min"], color=COLOR_MIN, linewidth=1.8,
            marker="o", markersize=4, label="min score")
    ax.plot(daily["date"], daily["score_max"], color=COLOR_MAX, linewidth=1.8,
            marker="o", markersize=4, label="max score")

    ax.axhline(0, color="#bdc3c7", linewidth=0.8, linestyle="--")
    ax.set_ylim(-1.05, 1.05)
    ax.set_xlabel("Date")
    ax.set_ylabel("Score")
    ax.set_title("Daily min / max NLP score — energy_br")
    ax.legend()

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=45)

    plt.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Plot saved → {out}")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    df = load(path)
    daily = aggregate(df)
    save_csv(daily, OUTPUT_CSV)
    plot(daily, OUTPUT_PNG)
    print(f"\n{len(daily)} days  |  score range [{daily['score_min'].min():.2f}, {daily['score_max'].max():.2f}]")


if __name__ == "__main__":
    main()
