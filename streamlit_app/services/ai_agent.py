import json
from typing import List, Type
from openai import AzureOpenAI
from pydantic import BaseModel
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


def get_deployment() -> str:
    return get_secret("AZURE_OPENAI_DEPLOYMENT_NAME", "corpu-text-gpt-4o")


def call_llm(
    system_prompt: str,
    user_message: str,
    context_chunks: List[str] = [],
    max_tokens: int = 4096,
) -> str:
    """Call Azure OpenAI GPT-4o with optional RAG context."""
    if context_chunks:
        context = "\n\n---\n\n".join(context_chunks)
        full_user_msg = f"Context:\n{context}\n\nTask:\n{user_message}"
    else:
        full_user_msg = user_message

    response = _get_client().chat.completions.create(
        model=get_deployment(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user_msg},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def parse_llm_json(raw: str, model: Type[BaseModel]) -> List[dict]:
    """Parse and validate JSON array from LLM response. Retries once on failure."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[-1] if cleaned.count("```") >= 2 else cleaned
        cleaned = cleaned.lstrip("json").strip().rstrip("```").strip()

    try:
        data = json.loads(cleaned)
        return [model(**item).model_dump() for item in data]
    except Exception:
        retry_response = call_llm(
            system_prompt="You are a JSON formatter. Return ONLY valid JSON array, no explanation, no markdown.",
            user_message=f"Fix this JSON and return only the valid JSON array:\n{raw}",
        )
        retry_cleaned = retry_response.strip().lstrip("```json").rstrip("```").strip()
        data = json.loads(retry_cleaned)
        return [model(**item).model_dump() for item in data]
