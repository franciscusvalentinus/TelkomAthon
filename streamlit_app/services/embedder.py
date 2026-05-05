import time
from typing import List
from openai import AzureOpenAI
try:
    from streamlit_app.services.config import get_secret
except ImportError:
    from config import get_secret  # type: ignore

_client = None


def _get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        _client = AzureOpenAI(
            azure_endpoint=get_secret("AZURE_OPENAI_ENDPOINT"),
            api_key=get_secret("AZURE_OPENAI_API_KEY"),
            api_version=get_secret("AZURE_OPENAI_API_VERSION"),
        )
    return _client


def get_embedding_model() -> str:
    return get_secret("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "corpu-text-embedding-3-large")


def embed_text(text: str, retries: int = 3) -> List[float]:
    for attempt in range(retries):
        try:
            response = _get_client().embeddings.create(
                input=text, model=get_embedding_model()
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise e


def embed_chunks(chunks: List[str]) -> List[List[float]]:
    return [embed_text(chunk) for chunk in chunks]
