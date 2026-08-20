import json
import os

from src.nlp.client import get_client


MODEL = os.environ.get(
    "AZURE_OPENAI_MODEL",
    "gpt-5.4-mini",
)


def analyze_news(
    title: str,
    summary: str,
    system_prompt: str,
) -> dict:

    client = get_client()

    user_input = f"""
Título:
{title}

Resumo:
{summary}
"""

    response = client.responses.create(
        model=MODEL,
        instructions=system_prompt,
        input=user_input,
    )

    return json.loads(response.output_text)