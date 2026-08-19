from html import unescape

import feedparser
import yaml
from bs4 import BeautifulSoup


#efine o caminho do arquivo de configuração do site
CONFIG_PATH = "config/sites/megawhat.yaml"


#le o arquivo YAML dps carrega as configurações em um dicionario
with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    cfg = yaml.safe_load(file)

# Pega a URL do RSS que esta salva na configuração
RSS_URL = cfg["url"]


def clean_html(value: str | None) -> str:
    # Se não vier valor retorna vazio
    if not value:
        return ""

    # Converte o HTML em texto limpo usando BeautifulSoup
    soup = BeautifulSoup(value, "html.parser")
    text = soup.get_text(" ", strip=True)

    #remove coisas de HTML como && <>  e outros codigos especiais
    text = unescape(text)

    #troca espaços especiais por espaço normal 
    text = text.replace("\xa0", " ")

    #remove espaços extras e quebras de linha em excesso
    text = " ".join(text.split())

    #re o texto tiver a frase "O post " remove tudo depois dela
    if "O post " in text:
        text = text.split("O post ")[0].strip()

    return text


def collect_news(limit: int = 10) -> list[dict]:
    # Faz o parse do feed RSS usando a URL configurada
    feed = feedparser.parse(RSS_URL)

    #lista para guardar as notícias
    news = []

    # Percorre as entradas do feed, até o limite informado
    for entry in feed.entries[:limit]:
        # Cria um dicionário com os dados da notícia
        item = {
            "source": cfg["site"],  # Nome do site
            "title": clean_html(entry.get("title")),  # Título limpo
            "url": entry.get("link", ""),  # Link da notícia
            "published_at": entry.get("published", ""),  # Data de publicação
            "summary": clean_html(entry.get("summary")),  # Resumo limpo
        }

        # Adiciona a notícia na lista
        news.append(item)

    return news


def main(): #somente para teste
    #Busca ate3 notícias
    news = collect_news(limit=3)

    # Mostra cada item da lista
    for item in news:
        print(item)
        print("-" * 80)


# Executa a função main quando o arquivo é rodado diretamente
if __name__ == "__main__":
    main()