#from html import unescape

import feedparser
import yaml
#from bs4 import BeautifulSoup


#efine o caminho do arquivo de configuração do site
CONFIG_PATH = "config/sites/megawhat.yaml"


#le o arquivo YAML dps carrega as configurações em um dicionario
with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    cfg = yaml.safe_load(file)

# Pega a URL do RSS que esta salva na configuração
RSS_URL = cfg["url"]


# Define uma funcao para coletar noticias.
def collect_news(limit: int = 10) -> list[dict]:
    """Coleta noticias do feed RSS do site MegaWhat."""
    #feed RSS configurado.
    feed = feedparser.parse(cfg["url"])

    # Cria uma lista vazia para armazenar as noticias.
    news = []

    # Percorre as noticias ate o limite informado.
    for entry in feed.entries[:limit]:
        # Cria um dicionario com os dados da noticia.
        item = {
            # Adiciona o nome do site.
            "source": cfg["site"],
            # Adiciona o titulo da noticia.
            "title": entry.get("title", ""),
            # Adiciona o resumo da noticia.
            "summary": entry.get("summary", ""),
            # Adiciona o link da noticia.
            "url": entry.get("link", ""),
            # Adiciona a data de publicacao.
            "published_at": entry.get("published", ""),
        }

        # Adiciona a noticia a lista final.
        news.append(item)

    # Retorna todas as noticias coletadas.
    return news

from src.normalization.megawhat import normalize_news
def main():
    news = collect_news(limit=3)

    for item in news:
        normalized = normalize_news(item)

        print(normalized)
        print("-" * 80)


# Executa a função main quando o arquivo é rodado diretamente
if __name__ == "__main__":
    main()