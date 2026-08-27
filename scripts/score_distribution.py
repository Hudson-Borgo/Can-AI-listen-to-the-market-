"""
Analyze the distribution of score and relevance in a processed NLP CSV.
Usage:
    python scripts/score_distribution.py data/processed/energy_br.csv
    python scripts/score_distribution.py baseline.csv new.csv   # side-by-side diff
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


BINS_SCORE = [-1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
BINS_RELEVANCE = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
SENTIMENT_COLORS = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}
SENTIMENT_ORDER = ["positive", "neutral", "negative"]


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in ("score", "relevance", "sentiment") if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    return df.dropna(subset=["score", "relevance"])


def describe(df: pd.DataFrame, label: str) -> None:
    n = len(df)
    print(f"\n{'='*60}")
    print(f"  {label}  (n={n})")
    print(f"{'='*60}")

    if n == 0:
        print("  No rows with score/relevance data.")
        return

    for col, bins in [("score", BINS_SCORE), ("relevance", BINS_RELEVANCE)]:
        print(f"\n-- {col} --")
        print(df[col].describe().round(3).to_string())
        counts = pd.cut(df[col], bins=bins, include_lowest=True).value_counts().sort_index()
        pcts = (counts / n * 100).round(1)
        print(f"\n{'Bin':<22} {'Count':>6}  {'%':>6}")
        for interval, count in counts.items():
            bar = "#" * int(pcts[interval] / 2)
            print(f"  {str(interval):<20} {count:>6}  {pcts[interval]:>5.1f}%  {bar}")

    print("\n-- sentiment --")
    sentiment_counts = df["sentiment"].value_counts()
    for sentiment, count in sentiment_counts.items():
        pct = count / n * 100
        bar = "#" * int(pct / 2)
        print(f"  {sentiment:<12} {count:>6}  {pct:>5.1f}%  {bar}")


def compare(df_a: pd.DataFrame, df_b: pd.DataFrame, label_a: str, label_b: str) -> None:
    print(f"\n{'='*60}")
    print(f"  COMPARISON: {label_a}  vs  {label_b}")
    print(f"{'='*60}")
    for col in ("score", "relevance"):
        a, b = df_a[col], df_b[col]
        print(f"\n-- {col} mean: {a.mean():.3f} -> {b.mean():.3f}  (Δ {b.mean()-a.mean():+.3f})")
        print(f"   {col} std:  {a.std():.3f} -> {b.std():.3f}  (Δ {b.std()-a.std():+.3f})")

    for sentiment in ("positive", "neutral", "negative"):
        pa = (df_a["sentiment"] == sentiment).mean() * 100
        pb = (df_b["sentiment"] == sentiment).mean() * 100
        print(f"   {sentiment:<12} {pa:>5.1f}% -> {pb:>5.1f}%  (Δ {pb-pa:+.1f}pp)")


def _short_label(path: str) -> str:
    return Path(path).stem


def plot_single(df: pd.DataFrame, label: str) -> plt.Figure:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle(label, fontsize=13, fontweight="bold")

    # score histogram
    ax = axes[0]
    ax.hist(df["score"], bins=BINS_SCORE, edgecolor="white", color="#3498db")
    ax.set_title("Score distribution")
    ax.set_xlabel("score")
    ax.set_ylabel("count")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.xaxis.set_major_locator(mticker.MultipleLocator(0.2))

    # relevance histogram
    ax = axes[1]
    ax.hist(df["relevance"], bins=BINS_RELEVANCE, edgecolor="white", color="#9b59b6")
    ax.set_title("Relevance distribution")
    ax.set_xlabel("relevance")
    ax.xaxis.set_major_locator(mticker.MultipleLocator(0.2))

    # sentiment bar
    ax = axes[2]
    counts = [df["sentiment"].value_counts().get(s, 0) for s in SENTIMENT_ORDER]
    colors = [SENTIMENT_COLORS[s] for s in SENTIMENT_ORDER]
    ax.bar(SENTIMENT_ORDER, counts, color=colors, edgecolor="white")
    ax.set_title("Sentiment breakdown")
    ax.set_ylabel("count")
    for i, v in enumerate(counts):
        if v:
            ax.text(i, v + 0.3, str(v), ha="center", fontsize=9)

    fig.tight_layout()
    return fig


def plot_compare(df_a: pd.DataFrame, df_b: pd.DataFrame, label_a: str, label_b: str) -> plt.Figure:
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle(f"Comparison: {label_a}  vs  {label_b}", fontsize=13, fontweight="bold")

    short_a, short_b = _short_label(label_a), _short_label(label_b)

    for row, (df, lbl) in enumerate([(df_a, short_a), (df_b, short_b)]):
        axes[row, 0].hist(df["score"], bins=BINS_SCORE, edgecolor="white", color="#3498db")
        axes[row, 0].set_title(f"Score — {lbl}")
        axes[row, 0].axvline(0, color="black", linewidth=0.8, linestyle="--")
        axes[row, 0].xaxis.set_major_locator(mticker.MultipleLocator(0.2))
        axes[row, 0].set_xlabel("score")
        axes[row, 0].set_ylabel("count")

        axes[row, 1].hist(df["relevance"], bins=BINS_RELEVANCE, edgecolor="white", color="#9b59b6")
        axes[row, 1].set_title(f"Relevance — {lbl}")
        axes[row, 1].xaxis.set_major_locator(mticker.MultipleLocator(0.2))
        axes[row, 1].set_xlabel("relevance")

        counts = [df["sentiment"].value_counts().get(s, 0) for s in SENTIMENT_ORDER]
        colors = [SENTIMENT_COLORS[s] for s in SENTIMENT_ORDER]
        axes[row, 2].bar(SENTIMENT_ORDER, counts, color=colors, edgecolor="white")
        axes[row, 2].set_title(f"Sentiment — {lbl}")
        for i, v in enumerate(counts):
            if v:
                axes[row, 2].text(i, v + 0.3, str(v), ha="center", fontsize=9)

    # align y-axes within each column so bars are comparable
    for col in range(3):
        y_max = max(axes[0, col].get_ylim()[1], axes[1, col].get_ylim()[1])
        axes[0, col].set_ylim(0, y_max)
        axes[1, col].set_ylim(0, y_max)

    # delta subplot replacing bottom-right: score KDE overlay
    axes[1, 2].remove()
    ax_kde = fig.add_subplot(2, 3, 6)
    for df, lbl, color in [(df_a, short_a, "#3498db"), (df_b, short_b, "#e67e22")]:
        df["score"].plot.kde(ax=ax_kde, label=lbl, color=color)
    ax_kde.set_title("Score KDE overlay")
    ax_kde.set_xlabel("score")
    ax_kde.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax_kde.legend(fontsize=8)

    fig.tight_layout()
    return fig


def main() -> None:
    paths = sys.argv[1:]
    if not paths:
        print("Usage: python scripts/score_distribution.py <csv> [<csv2>]")
        sys.exit(1)

    frames = [(p, load(p)) for p in paths]

    for path, df in frames:
        describe(df, path)

    if len(frames) == 2:
        compare(frames[0][1], frames[1][1], frames[0][0], frames[1][0])
        fig = plot_compare(frames[0][1], frames[1][1], frames[0][0], frames[1][0])
    else:
        fig = plot_single(frames[0][1], frames[0][0])

    plt.show()


if __name__ == "__main__":
    main()
