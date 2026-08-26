import os

from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv()


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-03-01-preview"),
        timeout=60.0,
        max_retries=0,
    )