import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard.data import load_energy_news
from src.signals.aggregate import calculate_daily_signals


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Can AI Listen to the Market?",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# LOAD DATA
# ============================================================
# Carrega:
#
# 1. O CSV enriquecido pelo LLM:
#    data/processed/energy_br.csv
#
# 2. A serie diaria calculada pelo Signal Aggregator:
#    src/signals/aggregate.py
# ============================================================

try:
    news = load_energy_news()
    daily_signals = calculate_daily_signals("energy_br")

except Exception as error:
    st.error(f"Unable to load market data: {error}")
    st.stop()


# ============================================================
# PREPARE DATES
# ============================================================
# A data passa a ser um filtro global da pagina.
#
# Ao selecionar outro dia:
# - Market Signal muda
# - Articles Analyzed muda
# - Average Relevance muda
# - News Feed muda
#
# O grafico continua mostrando todo o historico.
# ============================================================

news["date"] = news["published_at"].dt.date

available_dates = sorted(
    daily_signals["date"].dropna().unique(),
    reverse=True,
)

if not available_dates:
    st.error("No market dates available.")
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("Can AI Listen")
    st.caption("AI-powered market intelligence")

    st.divider()

    st.subheader("Market")
    st.markdown("**Energy Brazil**")

    st.divider()

    st.subheader("Market Date")

    selected_date = st.selectbox(
        "Select date",
        options=available_dates,
        index=0,
        label_visibility="collapsed",
    )

    st.divider()

    st.caption("Current dataset")
    st.code("energy_br.csv")


# ============================================================
# SELECT DAILY SIGNAL
# ============================================================
# Busca no Signal Aggregator os valores correspondentes
# a data selecionada pelo usuario.
# ============================================================

selected_signal = daily_signals[
    daily_signals["date"] == selected_date
].iloc[0]

current_signal = float(
    selected_signal["signal"]
)

current_trend = str(
    selected_signal["trend"]
)

articles_today = int(
    selected_signal["articles"]
)

average_relevance = float(
    selected_signal["average_relevance"]
)


# ============================================================
# HEADER
# ============================================================

st.title("Brazilian Energy Market")

st.caption(
    "AI-powered monitoring of news sentiment and "
    "market signals for the Brazilian energy sector."
)

st.divider()


# ============================================================
# MARKET OVERVIEW
# ============================================================
# Exibe o termometro correspondente a data selecionada.
# ============================================================

st.subheader("Market Overview")

st.caption(
    f"Market intelligence for {selected_date}"
)

signal_col, articles_col, relevance_col = st.columns(3)


# ------------------------------------------------------------
# MARKET SIGNAL
# ------------------------------------------------------------

with signal_col:

    st.metric(
        label="Market Signal",
        value=f"{current_signal:+.3f}",
        help="Weighted sentiment signal ranging from -1 to +1.",
    )

    if current_trend == "POSITIVE":
        st.success("POSITIVE")

    elif current_trend == "NEGATIVE":
        st.error("NEGATIVE")

    else:
        st.warning("NEUTRAL")


# ------------------------------------------------------------
# ARTICLES ANALYZED
# ------------------------------------------------------------

with articles_col:

    st.metric(
        label="Articles Analyzed",
        value=articles_today,
        help=(
            "Number of analyzed articles contributing "
            "to the market signal for the selected date."
        ),
    )


# ------------------------------------------------------------
# AVERAGE RELEVANCE
# ------------------------------------------------------------

with relevance_col:

    st.metric(
        label="Average Relevance",
        value=f"{average_relevance:.3f}",
        help=(
            "Average market relevance assigned by the "
            "AI model to the analyzed articles."
        ),
    )


st.divider()


# ============================================================
# SIGNAL HISTORY
# ============================================================
# Mostra toda a serie historica disponivel.
#
# O eixo Y fica fixo entre -1 e +1 porque essa e a escala
# oficial do nosso indicador.
#
# Tambem mostramos:
#
# +0.15 -> limite positivo
#  0.00 -> ponto neutro
# -0.15 -> limite negativo
# ============================================================

st.subheader("Daily Market Signal")

st.caption(
    "Historical evolution of the AI-generated market signal."
)


chart_data = daily_signals.copy()

chart_data["date"] = (
    chart_data["date"].astype(str)
)


# ------------------------------------------------------------
# MAIN SIGNAL LINE
# ------------------------------------------------------------

signal_line = (
    alt.Chart(chart_data)
    .mark_line(
        point=True,
        strokeWidth=3,
    )
    .encode(
        x=alt.X(
            "date:O",
            title="Date",
        ),
        y=alt.Y(
            "signal:Q",
            title="Market Signal",
            scale=alt.Scale(
                domain=[-1, 1]
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "date:O",
                title="Date",
            ),
            alt.Tooltip(
                "signal:Q",
                title="Signal",
                format=".3f",
            ),
            alt.Tooltip(
                "articles:Q",
                title="Articles",
            ),
            alt.Tooltip(
                "average_relevance:Q",
                title="Avg. Relevance",
                format=".3f",
            ),
            alt.Tooltip(
                "trend:N",
                title="Trend",
            ),
        ],
    )
)


# ------------------------------------------------------------
# ZERO LINE
# ------------------------------------------------------------

zero_line = (
    alt.Chart(
        {
            "values": [
                {"y": 0}
            ]
        }
    )
    .mark_rule(
        strokeDash=[5, 5]
    )
    .encode(
        y="y:Q"
    )
)


# ------------------------------------------------------------
# POSITIVE THRESHOLD
# ------------------------------------------------------------

positive_threshold = (
    alt.Chart(
        {
            "values": [
                {"y": 0.15}
            ]
        }
    )
    .mark_rule(
        strokeDash=[2, 2]
    )
    .encode(
        y="y:Q"
    )
)


# ------------------------------------------------------------
# NEGATIVE THRESHOLD
# ------------------------------------------------------------

negative_threshold = (
    alt.Chart(
        {
            "values": [
                {"y": -0.15}
            ]
        }
    )
    .mark_rule(
        strokeDash=[2, 2]
    )
    .encode(
        y="y:Q"
    )
)


chart = (
    signal_line
    + zero_line
    + positive_threshold
    + negative_threshold
)


st.altair_chart(
    chart,
    use_container_width=True,
)


# ============================================================
# SENTIMENT DISTRIBUTION
# ============================================================
# Mostra quantas noticias positivas, neutras e negativas
# contribuiram para o sinal do dia selecionado.
#
# Essa distribuicao NAO calcula o signal.
# Ela serve apenas como explicacao visual.
# ============================================================

st.divider()

st.subheader("Sentiment Distribution")


day_news = news[
    news["date"] == selected_date
].copy()


day_news = day_news.dropna(
    subset=[
        "sentiment",
        "score",
        "relevance",
    ]
)


sentiment_counts = (
    day_news["sentiment"]
    .str.lower()
    .value_counts()
)


positive_count = int(
    sentiment_counts.get(
        "positive",
        0,
    )
)

neutral_count = int(
    sentiment_counts.get(
        "neutral",
        0,
    )
)

negative_count = int(
    sentiment_counts.get(
        "negative",
        0,
    )
)


positive_col, neutral_col, negative_col = st.columns(3)


with positive_col:

    st.metric(
        "Positive Articles",
        positive_count,
    )


with neutral_col:

    st.metric(
        "Neutral Articles",
        neutral_count,
    )


with negative_col:

    st.metric(
        "Negative Articles",
        negative_count,
    )


# ============================================================
# NEWS FEED
# ============================================================
# O feed mostra somente noticias:
#
# - da data selecionada;
# - que ja passaram pelo LLM;
# - ordenadas da mais recente para a mais antiga.
#
# Por padrao mostramos no maximo 10 noticias.
# ============================================================

st.divider()

st.subheader("Energy News")

st.caption(
    "Articles contributing to the market signal "
    f"for {selected_date}."
)


# ------------------------------------------------------------
# SENTIMENT FILTER
# ------------------------------------------------------------

sentiment_filter = st.segmented_control(
    "Sentiment",
    options=[
        "All",
        "Positive",
        "Neutral",
        "Negative",
    ],
    default="All",
)


# ------------------------------------------------------------
# APPLY FILTER
# ------------------------------------------------------------

feed = day_news.copy()


if sentiment_filter != "All":

    feed = feed[
        feed["sentiment"].str.lower()
        == sentiment_filter.lower()
    ]


# ------------------------------------------------------------
# SORT ARTICLES
# ------------------------------------------------------------

feed = feed.sort_values(
    "published_at",
    ascending=False,
)


# ------------------------------------------------------------
# LIMIT FEED
# ------------------------------------------------------------

total_filtered = len(feed)

feed = feed.head(10)


st.caption(
    f"Showing {len(feed)} of "
    f"{total_filtered} matching articles."
)


# ============================================================
# ARTICLE CARDS
# ============================================================

if feed.empty:

    st.info(
        "No articles found for the selected filters."
    )


for _, article in feed.iterrows():

    sentiment = str(
        article["sentiment"]
    ).upper()

    score = float(
        article["score"]
    )

    relevance = float(
        article["relevance"]
    )

    published = article[
        "published_at"
    ]


    # --------------------------------------------------------
    # FORMAT DATE
    # --------------------------------------------------------

    if pd.notna(published):

        published_label = (
            published.strftime(
                "%d %b %Y · %H:%M UTC"
            )
        )

    else:

        published_label = (
            "Unknown date"
        )


    # --------------------------------------------------------
    # SENTIMENT BADGE
    # --------------------------------------------------------

    if sentiment == "POSITIVE":

        st.success(
            f"POSITIVE  ·  "
            f"Score {score:+.2f}  ·  "
            f"Relevance {relevance:.2f}"
        )

    elif sentiment == "NEGATIVE":

        st.error(
            f"NEGATIVE  ·  "
            f"Score {score:+.2f}  ·  "
            f"Relevance {relevance:.2f}"
        )

    else:

        st.warning(
            f"NEUTRAL  ·  "
            f"Score {score:+.2f}  ·  "
            f"Relevance {relevance:.2f}"
        )


    # --------------------------------------------------------
    # ARTICLE TITLE
    # --------------------------------------------------------

    st.markdown(
        f"### {article['title']}"
    )


    # --------------------------------------------------------
    # SOURCE + DATE
    # --------------------------------------------------------

    st.caption(
        f"{article['source']} "
        f"· {published_label}"
    )


    # --------------------------------------------------------
    # AI ANALYSIS
    # --------------------------------------------------------

    reason = article.get(
        "reason"
    )

    if pd.notna(reason):

        st.markdown(
            "**AI Analysis**"
        )

        st.write(
            reason
        )


    # --------------------------------------------------------
    # ORIGINAL ARTICLE
    # --------------------------------------------------------

    article_url = article.get(
        "url"
    )

    if pd.notna(article_url):

        st.link_button(
            "View original article ↗",
            article_url,
        )


    st.divider()


# ============================================================
# METHODOLOGY
# ============================================================
# Mantemos a metodologia no final da pagina porque ela e
# informacao complementar, nao o foco principal do dashboard.
# ============================================================

with st.expander(
    "How is the market signal calculated?"
):

    st.markdown(
        """
The daily market signal combines the sentiment score and
market relevance assigned by the AI model to each article.

### Formula

`Σ(score × relevance) / Σ(relevance)`

Each article receives two numerical values:

- **Score:** market sentiment ranging from **-1 to +1**
- **Relevance:** estimated market relevance ranging from **0 to 1**

Articles with higher relevance therefore have a greater
influence on the daily market signal.

### Classification

- **Positive:** signal > +0.15
- **Neutral:** -0.15 ≤ signal ≤ +0.15
- **Negative:** signal < -0.15

The thresholds are heuristic values defined for this
proof of concept and have not been historically calibrated.
"""
    )