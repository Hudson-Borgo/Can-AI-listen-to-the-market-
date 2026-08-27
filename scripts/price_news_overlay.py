"""
Interactive price line + high-conviction news event overlay.

Usage:
    python scripts/price_news_overlay.py
    python scripts/price_news_overlay.py <news_csv> <price_csv>

Threshold: |score| >= 0.75 selects high-conviction events.
Output: data/processed/price_news_overlay.html  (self-contained, needs CDN for plotly.js)
"""

import sys
from pathlib import Path

import pandas as pd

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    sys.exit("plotly is not installed.  Run: pip install plotly")

SCORE_THRESHOLD = 0.75
DEFAULT_NEWS  = Path("data/processed/energy_br.csv")
DEFAULT_PRICE = Path("data/processed/agg_diária_M1_2026 1.csv")
OUTPUT_HTML   = Path("data/processed/price_news_overlay.html")

COLOR_POS   = "#2ecc71"
COLOR_NEG   = "#e74c3c"
COLOR_CLOSE = "#2c3e50"
COLOR_ROLL  = "#8e44ad"

MAX_BAND_OPACITY = 0.18   # per-event ceiling; opacity = |score| * relevance * MAX
ROLL_WINDOW      = "31D"


def load_price(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["dia"])
    return df.rename(columns={"dia": "date"}).sort_values("date").reset_index(drop=True)


def load_events(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = (
        pd.to_datetime(df["published_at"], utc=True)
        .dt.tz_convert(None)
        .dt.normalize()
    )
    df = df[df["score"].abs() >= SCORE_THRESHOLD].copy()
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
    return df.sort_values("date").reset_index(drop=True)


ROLL_THRESHOLD = 0.5  # only news with |score| > this feed the rolling average


def load_rolling_score(path: Path) -> pd.Series:
    """14-day relevance-weighted rolling score, filtered to |score| > ROLL_THRESHOLD.

    Formula: sum(score_i * relevance_i) / sum(relevance_i) over the rolling window.
    """
    df = pd.read_csv(path)
    df["date"] = (
        pd.to_datetime(df["published_at"], utc=True)
        .dt.tz_convert(None)
        .dt.normalize()
    )
    df = df.dropna(subset=["score", "relevance"])
    df = df[df["score"].abs() > ROLL_THRESHOLD]
    df["wsum"] = df["score"] * df["relevance"]
    daily_wsum = df.groupby("date")["wsum"].sum()
    daily_wden = df.groupby("date")["relevance"].sum()
    daily_wsum.index = pd.to_datetime(daily_wsum.index)
    daily_wden.index = pd.to_datetime(daily_wden.index)
    roll_wsum = daily_wsum.rolling(ROLL_WINDOW, min_periods=1).sum()
    roll_wden = daily_wden.rolling(ROLL_WINDOW, min_periods=1).sum()
    return (roll_wsum / roll_wden).rename("rolling_score")


def snap_to_prior_trading_day(
    news_dates: pd.Series, trading_dates: pd.DatetimeIndex
) -> pd.Series:
    """Return the most recent trading date on or before each news date."""
    positions = trading_dates.searchsorted(news_dates.values, side="right") - 1
    result = pd.Series(pd.NaT, index=news_dates.index, dtype="datetime64[ns]")
    mask = positions >= 0
    result.loc[mask] = trading_dates[positions[mask]].values
    return result


def build_figure(
    price: pd.DataFrame,
    events: pd.DataFrame,
    rolling: pd.Series,
) -> go.Figure:
    trading_dates = pd.DatetimeIndex(price["date"])
    events = events.copy()
    events["snap_date"] = snap_to_prior_trading_day(events["date"], trading_dates)
    events = events.dropna(subset=["snap_date"])

    # y-position for markers: closing price on the snapped trading day
    price_lookup = price.set_index("date")["preco_fecho"]
    events["price_y"] = events["snap_date"].map(price_lookup)

    pos_ev = events[events["score"] >= SCORE_THRESHOLD]
    neg_ev = events[events["score"] <= -SCORE_THRESHOLD]

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.85, 0.15],
        shared_xaxes=True,
        vertical_spacing=0.02,
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
        subplot_titles=(
            f"M1 Price (€/MWh) + high-conviction news  (|score| ≥ {SCORE_THRESHOLD})",
            "Event density",
        ),
    )

    # --- Price band (min–max shaded area) ---
    fig.add_trace(
        go.Scatter(
            x=price["date"], y=price["preco_min"],
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=price["date"], y=price["preco_max"],
            fill="tonexty", fillcolor="rgba(189,195,199,0.4)",
            line=dict(width=0), name="Price range (min–max)", hoverinfo="skip",
        ),
        row=1, col=1,
    )

    # --- Closing price line ---
    fig.add_trace(
        go.Scatter(
            x=price["date"], y=price["preco_fecho"],
            line=dict(color=COLOR_CLOSE, width=1.8),
            name="Close price",
            hovertemplate="%{x|%Y-%m-%d}  Close: <b>%{y:.1f} €/MWh</b><extra></extra>",
        ),
        row=1, col=1,
    )

    # --- Rolling score line (all news, 14-day window, secondary y-axis) ---
    fig.add_trace(
        go.Scatter(
            x=rolling.index,
            y=rolling.values,
            line=dict(color=COLOR_ROLL, width=1.4, dash="dot"),
            name=f"{ROLL_WINDOW} rolling score (|score|>{ROLL_THRESHOLD})",
            hovertemplate="%{x|%Y-%m-%d}  Score: <b>%{y:.2f}</b><extra></extra>",
        ),
        row=1, col=1, secondary_y=True,
    )

    # --- 1-month impact windows: opacity weighted by |score| * relevance ---
    shapes = []
    for _, ev in events.iterrows():
        opacity = float(abs(ev["score"]) * ev["relevance"] * MAX_BAND_OPACITY)
        r, g, b = (46, 204, 113) if ev["score"] > 0 else (231, 76, 60)
        fill = f"rgba({r},{g},{b},{opacity:.3f})"
        shapes.append(dict(
            type="rect", xref="x", yref="paper",
            x0=ev["snap_date"],
            x1=ev["snap_date"] + pd.DateOffset(months=1),
            y0=0, y1=1,
            fillcolor=fill, line_width=0, layer="below",
        ))

    # --- Event markers ---
    for ev_df, symbol, color, label in (
        (pos_ev, "triangle-up",   COLOR_POS, f"Positive (≥+{SCORE_THRESHOLD})"),
        (neg_ev, "triangle-down", COLOR_NEG, f"Negative (≤−{SCORE_THRESHOLD})"),
    ):
        if ev_df.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=ev_df["snap_date"],
                y=ev_df["price_y"],
                mode="markers",
                marker=dict(
                    symbol=symbol, size=11, color=color,
                    line=dict(color="white", width=0.8),
                ),
                name=label,
                customdata=ev_df[["title", "score", "source", "date_str"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Score: %{customdata[1]:.2f}  ·  %{customdata[2]}<br>"
                    "Published: %{customdata[3]}<extra></extra>"
                ),
            ),
            row=1, col=1,
        )

    # --- Rug strip (bottom panel) ---
    for ev_df, color in ((pos_ev, COLOR_POS), (neg_ev, COLOR_NEG)):
        if ev_df.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=ev_df["snap_date"],
                y=[0.5] * len(ev_df),
                mode="markers",
                marker=dict(
                    symbol="line-ns", size=16, color=color,
                    line=dict(width=2, color=color),
                ),
                showlegend=False, hoverinfo="skip",
            ),
            row=2, col=1,
        )

    fig.update_layout(
        shapes=shapes,
        hovermode="closest",
        height=680,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=90, b=50),
    )
    fig.update_yaxes(title_text="€/MWh", secondary_y=False, row=1, col=1)
    fig.update_yaxes(
        title_text="Score", range=[-1.1, 1.1],
        secondary_y=True, row=1, col=1,
        showgrid=False, zeroline=True, zerolinecolor="#dfe6e9",
    )
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)

    return fig


def main() -> None:
    news_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_NEWS
    price_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PRICE

    for p in (news_path, price_path):
        if not p.exists():
            sys.exit(f"File not found: {p}")

    price   = load_price(price_path)
    events  = load_events(news_path)
    rolling = load_rolling_score(news_path)

    n_pos = (events["score"] >= SCORE_THRESHOLD).sum()
    n_neg = (events["score"] <= -SCORE_THRESHOLD).sum()
    print(f"Price rows: {len(price)}  |  Events: {len(events)}  (+{n_pos} / -{n_neg})")

    fig = build_figure(price, events, rolling)
    fig.write_html(OUTPUT_HTML, include_plotlyjs="cdn")
    print(f"HTML saved → {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
