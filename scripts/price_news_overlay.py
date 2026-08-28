"""
Interactive price line + high-conviction news event overlay.

Usage:
    python scripts/price_news_overlay.py
    python scripts/price_news_overlay.py <news_csv> <price_csv>

Threshold: |score| >= SCORE_THRESHOLD selects high-conviction events.
Output: data/processed/price_news_overlay.html  (self-contained, needs CDN for plotly.js)

Toggle visualizations via the VizConfig flags (see CONFIG below or --help style edits).
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    sys.exit("plotly is not installed.  Run: pip install plotly")


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DEFAULT_NEWS  = Path("data/processed/energy_br.csv")
DEFAULT_PRICE = Path("data/processed/agg_diária_M1_2026 1.csv")
OUTPUT_HTML   = Path("data/processed/price_news_overlay.html")

COLOR_POS   = "#2ecc71"
COLOR_NEG   = "#e74c3c"
COLOR_CLOSE = "#2c3e50"
COLOR_ROLL  = "#8e44ad"

RGB_POS = (46, 204, 113)
RGB_NEG = (231, 76, 60)


# --------------------------------------------------------------------------- #
# Configuration — flip flags here to turn visualizations on/off
# --------------------------------------------------------------------------- #
@dataclass
class VizConfig:
    # --- Analysis parameters ---
    score_threshold: float = 0.70   # |score| >= this selects high-conviction events
    roll_threshold: float = 0.30    # only news with |score| > this feed the rolling avg
    roll_window: str = "14D"
    max_band_opacity: float = 0.18  # per-event ceiling for impact-window shading

    # --- Visualization toggles ---
    show_price_band: bool = True        # min–max shaded area
    show_close_line: bool = True        # closing price line
    show_rolling_score: bool = True     # 14-day rolling score (secondary y-axis)
    show_impact_windows: bool = True    # 1-month shaded impact rectangles
    show_event_markers: bool = True     # triangle markers on the price line
    show_rug_strip: bool = True         # bottom event-density panel

    # --- Layout ---
    height: int = 680

    def __post_init__(self):
        # The bottom rug panel only makes sense as its own row.
        self.two_row_layout = self.show_rug_strip


CONFIG = VizConfig()


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_price(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["dia"])
    return df.rename(columns={"dia": "date"}).sort_values("date").reset_index(drop=True)


def load_events(path: Path, cfg: VizConfig) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = (
        pd.to_datetime(df["published_at"], utc=True)
        .dt.tz_convert(None)
        .dt.normalize()
    )
    df = df[df["score"].abs() >= cfg.score_threshold].copy()
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
    return df.sort_values("date").reset_index(drop=True)


def load_rolling_score(path: Path, cfg: VizConfig) -> pd.Series:
    """14-day relevance-weighted rolling score, filtered to |score| > roll_threshold.

    Formula: sum(score_i * relevance_i) / sum(relevance_i) over the rolling window.
    """
    df = pd.read_csv(path)
    df["date"] = (
        pd.to_datetime(df["published_at"], utc=True)
        .dt.tz_convert(None)
        .dt.normalize()
    )
    df = df.dropna(subset=["score", "relevance"])
    df = df[df["score"].abs() > cfg.roll_threshold]
    df["wsum"] = df["score"] * df["relevance"]
    daily_wsum = df.groupby("date")["wsum"].sum()
    daily_wden = df.groupby("date")["relevance"].sum()
    daily_wsum.index = pd.to_datetime(daily_wsum.index)
    daily_wden.index = pd.to_datetime(daily_wden.index)
    roll_wsum = daily_wsum.rolling(cfg.roll_window, min_periods=1).sum()
    roll_wden = daily_wden.rolling(cfg.roll_window, min_periods=1).sum()
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


def prepare_events(price: pd.DataFrame, events: pd.DataFrame, cfg: VizConfig) -> pd.DataFrame:
    """Snap events to trading days and attach the y-position (close price)."""
    trading_dates = pd.DatetimeIndex(price["date"])
    events = events.copy()
    events["snap_date"] = snap_to_prior_trading_day(events["date"], trading_dates)
    events = events.dropna(subset=["snap_date"])
    price_lookup = price.set_index("date")["preco_fecho"]
    events["price_y"] = events["snap_date"].map(price_lookup)
    return events


# --------------------------------------------------------------------------- #
# Individual visualization layers
# --------------------------------------------------------------------------- #
def add_price_band(fig: go.Figure, price: pd.DataFrame) -> None:
    """Min–max shaded area."""
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


def add_close_line(fig: go.Figure, price: pd.DataFrame) -> None:
    """Closing price line."""
    fig.add_trace(
        go.Scatter(
            x=price["date"], y=price["preco_fecho"],
            line=dict(color=COLOR_CLOSE, width=1.8),
            name="Close price",
            hovertemplate="%{x|%Y-%m-%d}  Close: <b>%{y:.1f} €/MWh</b><extra></extra>",
        ),
        row=1, col=1,
    )


def add_rolling_score(fig: go.Figure, rolling: pd.Series, cfg: VizConfig) -> None:
    """Rolling score line on the secondary y-axis."""
    fig.add_trace(
        go.Scatter(
            x=rolling.index, y=rolling.values,
            line=dict(color=COLOR_ROLL, width=1.4, dash="dot"),
            name=f"{cfg.roll_window} rolling score (|score|>{cfg.roll_threshold})",
            hovertemplate="%{x|%Y-%m-%d}  Score: <b>%{y:.2f}</b><extra></extra>",
        ),
        row=1, col=1, secondary_y=True,
    )


def build_impact_windows(events: pd.DataFrame, cfg: VizConfig) -> list:
    """Return a list of rectangle shapes (1-month impact windows)."""
    shapes = []
    for _, ev in events.iterrows():
        opacity = float(abs(ev["score"]) * ev["relevance"] * cfg.max_band_opacity)
        r, g, b = RGB_POS if ev["score"] > 0 else RGB_NEG
        shapes.append(dict(
            type="rect", xref="x", yref="paper",
            x0=ev["snap_date"],
            x1=ev["snap_date"] + pd.DateOffset(months=1),
            y0=0, y1=1,
            fillcolor=f"rgba({r},{g},{b},{opacity:.3f})",
            line_width=0, layer="below",
        ))
    return shapes


def add_event_markers(fig: go.Figure, pos_ev: pd.DataFrame, neg_ev: pd.DataFrame, cfg: VizConfig) -> None:
    """Triangle markers on the price line (alpha = |score| × relevance)."""
    for ev_df, symbol, rgb, label in (
        (pos_ev, "triangle-up",   RGB_POS, f"Positive (≥+{cfg.score_threshold})"),
        (neg_ev, "triangle-down", RGB_NEG, f"Negative (≤−{cfg.score_threshold})"),
    ):
        if ev_df.empty:
            continue
        alphas = (ev_df["score"].abs() * ev_df["relevance"]).clip(upper=1.0)
        colors = [f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{a:.3f})" for a in alphas]
        fig.add_trace(
            go.Scatter(
                x=ev_df["snap_date"], y=ev_df["price_y"],
                mode="markers",
                marker=dict(
                    symbol=symbol, size=11, color=colors,
                    line=dict(color="white", width=0.8),
                ),
                name=label,
                customdata=ev_df[["title", "score", "relevance", "source", "date_str"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Score: %{customdata[1]:.2f}  ·  Relevance: %{customdata[2]:.2f}<br>"
                    "%{customdata[3]}  ·  %{customdata[4]}<extra></extra>"
                ),
            ),
            row=1, col=1,
        )


def add_rug_strip(fig: go.Figure, pos_ev: pd.DataFrame, neg_ev: pd.DataFrame, rug_row: int) -> None:
    """Event-density rug strip on the bottom panel."""
    for ev_df, color in ((pos_ev, COLOR_POS), (neg_ev, COLOR_NEG)):
        if ev_df.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=ev_df["snap_date"], y=[0.5] * len(ev_df),
                mode="markers",
                marker=dict(
                    symbol="line-ns", size=16, color=color,
                    line=dict(width=2, color=color),
                ),
                showlegend=False, hoverinfo="skip",
            ),
            row=rug_row, col=1,
        )


# --------------------------------------------------------------------------- #
# Figure assembly
# --------------------------------------------------------------------------- #
def build_figure(
    price: pd.DataFrame,
    events: pd.DataFrame,
    rolling: pd.Series,
    cfg: VizConfig = CONFIG,
) -> go.Figure:
    events = prepare_events(price, events, cfg)
    pos_ev = events[events["score"] >= cfg.score_threshold]
    neg_ev = events[events["score"] <= -cfg.score_threshold]

    # Does the top panel need a secondary y-axis?
    secondary_y = cfg.show_rolling_score

    # --- Build subplot skeleton (1 or 2 rows depending on the rug strip) ---
    if cfg.two_row_layout:
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.85, 0.15],
            shared_xaxes=True,
            vertical_spacing=0.02,
            specs=[[{"secondary_y": secondary_y}], [{"secondary_y": False}]],
            subplot_titles=(
                f"M1 Price (€/MWh) + high-conviction news  (|score| ≥ {cfg.score_threshold})",
                "Event density",
            ),
        )
        rug_row = 2
    else:
        fig = make_subplots(
            rows=1, cols=1,
            specs=[[{"secondary_y": secondary_y}]],
            subplot_titles=(
                f"M1 Price (€/MWh) + high-conviction news  (|score| ≥ {cfg.score_threshold})",
            ),
        )
        rug_row = None

    # --- Layers (each guarded by its flag) ---
    if cfg.show_price_band:
        add_price_band(fig, price)

    if cfg.show_close_line:
        add_close_line(fig, price)

    if cfg.show_rolling_score:
        add_rolling_score(fig, rolling, cfg)

    shapes = build_impact_windows(events, cfg) if cfg.show_impact_windows else []

    if cfg.show_event_markers:
        add_event_markers(fig, pos_ev, neg_ev, cfg)

    if cfg.show_rug_strip and rug_row is not None:
        add_rug_strip(fig, pos_ev, neg_ev, rug_row)

    # --- Layout ---
    fig.update_layout(
        shapes=shapes,
        hovermode="closest",
        height=cfg.height,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=90, b=50),
    )
    fig.update_yaxes(title_text="€/MWh", secondary_y=False, row=1, col=1)
    if secondary_y:
        fig.update_yaxes(
            title_text="Score", range=[-1.1, 1.1],
            secondary_y=True, row=1, col=1,
            showgrid=False, zeroline=True, zerolinecolor="#dfe6e9",
        )

    if cfg.two_row_layout:
        fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
    else:
        fig.update_xaxes(title_text="Date", row=1, col=1)

    return fig


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    cfg = CONFIG
    news_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_NEWS
    price_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PRICE

    for p in (news_path, price_path):
        if not p.exists():
            sys.exit(f"File not found: {p}")

    price   = load_price(price_path)
    events  = load_events(news_path, cfg)
    rolling = load_rolling_score(news_path, cfg) if cfg.show_rolling_score else pd.Series(dtype=float)

    n_pos = (events["score"] >= cfg.score_threshold).sum()
    n_neg = (events["score"] <= -cfg.score_threshold).sum()
    print(f"Price rows: {len(price)}  |  Events: {len(events)}  (+{n_pos} / -{n_neg})")

    fig = build_figure(price, events, rolling, cfg)
    fig.write_html(OUTPUT_HTML, include_plotlyjs="cdn")
    print(f"HTML saved → {OUTPUT_HTML}")

CONFIG = VizConfig(
    show_rolling_score=False,
    show_impact_windows=False,
    show_rug_strip=False,
)

if __name__ == "__main__":
    main()
