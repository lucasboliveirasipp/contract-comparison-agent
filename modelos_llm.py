"""Fábrica do modelo de linguagem usado pelos analisadores de contrato."""

import os

from langchain_openai import AzureChatOpenAI


def get_model(model_name: str | None = None) -> AzureChatOpenAI:
    """Cria o cliente Azure OpenAI a partir das variáveis do .env.

    O nome do deployment vem do argumento ou de GPT4 (padrão: gpt-4o-mini).
    """
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        api_key=os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY", ""),
        api_version=os.getenv("API_VERSION", "2024-08-01-preview"),
        azure_deployment=model_name or os.getenv("GPT4", "gpt-4o-mini"),
        temperature=float(os.getenv("MODEL_TEMPERATURE", "0")),
    )
