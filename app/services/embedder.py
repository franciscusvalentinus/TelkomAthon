import os
import time
from typing import List
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "corpu-text-embedding-3-large")


def embed_text(text: str, retries: int = 3) -> List[float]:
    """Embed a single text string. Retries with exponential backoff on failure."""
    for attempt in range(retries):
        try:
            response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
            return response.data[0].embedding
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise e


def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """Embed a list of text chunks."""
    return [embed_text(chunk) for chunk in chunks]
