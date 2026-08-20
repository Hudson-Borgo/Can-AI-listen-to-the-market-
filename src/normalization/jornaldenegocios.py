from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from bs4 import BeautifulSoup


def clean_html(value: str | None) -> str:
    """Remove tags HTML e normaliza o texto."""
    if not value:
        return ""

    soup = BeautifulSoup(value, "html.parser")
    text = soup.get_text(" ", strip=True)

    text = unescape(text)
    text = text.replace("\xa0", " ")
    text = " ".join(text.split())

    return text


def normalize_published_at(value: str) -> str:
    """Converte a data de publicacao do feed RSS para o formato ISO 8601."""
    if not value:
        return ""

    published_at = parsedate_to_datetime(value)

    return published_at.isoformat()


def normalize_news(item: dict) -> dict:
    """Normaliza os campos de uma noticia coletada do feed RSS do Jornal de Negócios."""
    return {
        "source": item.get("source", ""),
        "title": clean_html(item.get("title")),
        "summary": clean_html(item.get("summary")),
        "url": item.get("url", ""),
        "published_at": normalize_published_at(
            item.get("published_at", "")
        ),
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "category": item.get("category", ""),
    }
