import feedparser
import yaml

CONFIG_PATH = "config/sites/eco.yaml"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    cfg = yaml.safe_load(file)

RSS_URL = cfg["url"]


def collect_news(limit: int = 100) -> list[dict]:
    """Coleta noticias do feed RSS do site ECO."""
    feed = feedparser.parse(cfg["url"])

    news = []

    for entry in feed.entries[:limit]:
        item = {
            "source": cfg["site"],
            "title": entry.get("title", ""),
            "summary": entry.get("summary", ""),
            "url": entry.get("link", ""),
            "published_at": entry.get("published", ""),
            "category": cfg["category"],
        }

        news.append(item)

    return news


from src.normalization.eco import normalize_news


def main():
    news = collect_news(limit=3)

    for item in news:
        normalized = normalize_news(item)

        print(normalized)
        print("-" * 80)


if __name__ == "__main__":
    main()
