import json
import os
from typing import Optional

from openai import AzureOpenAI

from src.nlp.client import get_client


MODEL = os.environ.get(
    "AZURE_OPENAI_MODEL",
    "gpt-5.4-mini",
)


def analyze_news(
    title: str,
    summary: str,
    system_prompt: str,
    client: Optional[AzureOpenAI] = None,
) -> dict:

    if client is None:
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