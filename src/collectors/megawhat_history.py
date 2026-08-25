import argparse
from datetime import datetime, timezone
from pathlib import Path
import time

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import requests
from bs4 import BeautifulSoup

from src.repository.news_repository import save_news


BASE_URL = "https://megawhat.uol.com.br/ultimas-noticias/"
SOURCE = "megawhat"
CATEGORY = "energy_br"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    )
}

def create_session() -> requests.Session:
    """
    Cria uma sessao HTTP reutilizavel com retry automatico.
    """

    session = requests.Session()

    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=1,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session.mount(
        "https://",
        adapter,
    )

    session.headers.update(
        HEADERS
    )

    return session


SESSION = create_session()




def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect historical MegaWhat news."
    )

    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--end-date",
        required=True,
        help="End date in YYYY-MM-DD format.",
    )

    return parser.parse_args()


def parse_date(value: str) -> datetime:
    return datetime.strptime(
        value,
        "%Y-%m-%d",
    ).replace(
        tzinfo=timezone.utc
    )


def get_page_url(page: int) -> str:
    if page == 1:
        return BASE_URL

    return f"{BASE_URL}page/{page}/"


def get_article_published_at(
    url: str,
) -> str:
    """
    Abre uma materia e extrai a data oficial de publicacao
    a partir do metadata article:published_time.
    """

    try:
        response = SESSION.get(
            url,
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(
            f"      ⚠ Failed to read article: "
            f"{url}"
        )

        print(
            f"        {error}"
        )

        return ""

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    meta = soup.find(
        "meta",
        attrs={
            "property": "article:published_time"
        },
    )

    if not meta:
        return ""

    return meta.get(
        "content","",)


def collect_page(page: int) -> list[dict]:
    page_url = get_page_url(page)

    response = SESSION.get(
        page_url,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    articles = soup.select(
        "article.feed.feed-lg-v1"
    )

    news = []

    for article in articles:
        link = article.select_one(
            "a.feed-link"
        )

        title = article.select_one(
            "h2.feed-title"
        )

        summary = article.select_one(
            "p.feed-excert"
        )

        if not link or not title:
            continue

        url = link.get(
            "href",
            "",
        )

        published_at = (
            get_article_published_at(url)
        )

        item = {
            "source": SOURCE,
            "title": title.get_text(
                " ",
                strip=True,
            ),
            "summary": (
                summary.get_text(
                    " ",
                    strip=True,
                )
                if summary
                else ""
            ),
            "url": url,
            "published_at": published_at,
            "fetched_at": datetime.now(
                timezone.utc
            )
            .replace(microsecond=0)
            .isoformat(),
            "category": CATEGORY,
        }

        news.append(item)

        # Pequena pausa para não fazer requisições
        # muito agressivas ao site.
        time.sleep(0.8)

    return news


def collect_history(
    start_date: datetime,
    end_date: datetime,
) -> list[dict]:

    collected = []
    page = 1
    stop = False

    print("\n" + "=" * 70)
    print("  MEGAWHAT HISTORICAL COLLECTION")
    print("=" * 70)

    print(
        f"\nPeriod   : "
        f"{start_date.date()} → {end_date.date()}"
    )

    print(f"Category : {CATEGORY}")

    while not stop:
        print(
            f"\nPage {page}..."
        )

        page_news = collect_page(page)

        if not page_news:
            print(
                "No more articles found."
            )
            break

        added_this_page = 0

        for item in page_news:
            if not item["published_at"]:
                continue

            published_at = (
                datetime.fromisoformat(
                    item["published_at"]
                )
            )

            # Ainda estamos depois do período desejado.
            if published_at > end_date:
                continue

            # Chegamos antes do início.
            if published_at < start_date:
                stop = True
                break

            collected.append(item)
            added_this_page += 1

        print(
            f"      Articles in range: "
            f"{added_this_page}"
        )

        page += 1

    return collected


def main():
    args = parse_args()

    start_date = parse_date(
        args.start_date
    )

    # Inclui o dia inteiro informado em end-date.
    end_date = parse_date(
        args.end_date
    ).replace(
        hour=23,
        minute=59,
        second=59,
    )

    news = collect_history(
        start_date=start_date,
        end_date=end_date,
    )

    print(
        f"\nCollected in period: "
        f"{len(news)}"
    )

    if not news:
        print(
            "\nNo articles found "
            "for the requested period."
        )
        return

    result = save_news(
        news
    )

    print("\n" + "-" * 70)

    print(
        f"Received   : "
        f"{result['received']}"
    )

    print(
        f"New        : "
        f"{result['inserted']}"
    )

    print(
        f"Duplicates : "
        f"{result['duplicates']}"
    )

    print(
        f"Total      : "
        f"{result['total']}"
    )

    print("\n" + "=" * 70)
    print(
        "  ✓ HISTORICAL COLLECTION COMPLETED"
    )
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()