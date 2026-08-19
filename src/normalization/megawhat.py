from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from bs4 import BeautifulSoup



def clean_html(value: str | None) -> str:
    """Remove tags HTML e normaliza o texto."""
    # Retorna texto vazio quando nao existe valor.
    if not value:
        return ""

    # Cria um analisador para o conteudo HTML.
    soup = BeautifulSoup(value, "html.parser")
    # Extrai somente o texto, separando os elementos por espaco.
    text = soup.get_text(" ", strip=True)

    # Converte entidades HTML para caracteres normais.
    text = unescape(text)
    # Troca espacos especiais por espacos comuns.
    text = text.replace("\xa0", " ")
    # Remove espacos duplicados do texto.
    text = " ".join(text.split())

    # Verifica se o texto possui o marcador de fim do conteudo.
    if "O post " in text:
        # Remove o marcador e tudo que aparece depois dele.
        text = text.split("O post ")[0].strip()

    # Retorna o texto limpo.
    return text


def normalize_published_at(value: str) -> str:
    """Converte a data de publicacao do feed RSS para o formato ISO 8601."""
    # Retorna texto vazio quando nao existe data.
    if not value:
        return ""

    # Converte a data do RSS para um objeto datetime.
    published_at = parsedate_to_datetime(value)

    # Retorna a data no formato ISO 8601.
    return published_at.isoformat()



def normalize_news(item: dict) -> dict:
    """ Normaliza os campos de uma noticia coletada do feed RSS do site MegaWhat."""
    # Retorna um dicionario com os dados padronizados.
    return {
        # Mantem o nome da fonte da noticia.
        "source": item.get("source", ""),
        # Limpa o HTML do titulo.
        "title": clean_html(item.get("title")),
        # Limpa o HTML do resumo.
        "summary": clean_html(item.get("summary")),
        # Mantem o endereco da noticia.
        "url": item.get("url", ""),
        # Converte a data de publicacao para ISO 8601.
        "published_at": normalize_published_at(
            # Busca a data original da noticia.
            item.get("published_at", "")
        ),
        # Registra o momento em que a noticia foi coletada.
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }