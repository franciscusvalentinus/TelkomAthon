import os
import json
from typing import List, Type
from openai import AzureOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "corpu-text-gpt-4o")


def call_llm(system_prompt: str, user_message: str, context_chunks: List[str] = []) -> str:
    """Call Azure OpenAI GPT-4o with optional RAG context injected into user message."""
    if context_chunks:
        context = "\n\n---\n\n".join(context_chunks)
        full_user_msg = f"Context:\n{context}\n\nTask:\n{user_message}"
    else:
        full_user_msg = user_message

    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user_msg},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def parse_llm_json(raw: str, model: Type[BaseModel]) -> List[dict]:
    """
    Parse and validate JSON array from LLM response.
    Strips markdown code fences, validates each item with Pydantic model.
    Retries once with a stricter prompt if parsing fails.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[-1] if cleaned.count("```") >= 2 else cleaned
        cleaned = cleaned.lstrip("json").strip().rstrip("```").strip()

    try:
        data = json.loads(cleaned)
        return [model(**item).model_dump() for item in data]
    except Exception:
        # Retry: ask LLM to return only valid JSON
        retry_response = call_llm(
            system_prompt="You are a JSON formatter. Return ONLY valid JSON array, no explanation, no markdown.",
            user_message=f"Fix this JSON and return only the valid JSON array:\n{raw}",
        )
        retry_cleaned = retry_response.strip().lstrip("```json").rstrip("```").strip()
        data = json.loads(retry_cleaned)
        return [model(**item).model_dump() for item in data]
