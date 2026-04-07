"""
Singleton Groq API client wrapper with retry logic.
"""

import time
from groq import Groq
from config.settings import settings
from shared.logger import log_llm_call

_client: Groq | None = None


def get_groq_client() -> Groq:
    """Get or create the singleton Groq client."""
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def call_llm(system_prompt: str, user_message: str,
             temperature: float = 0.3, max_retries: int = 3) -> str:
    """
    Single LLM call with retry + logging.
    temperature=0.3 for consistent, deterministic agent outputs.
    Returns the response text.
    """
    client = get_groq_client()

    for attempt in range(max_retries):
        try:
            start = time.time()
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=2048
            )
            latency = time.time() - start
            result = response.choices[0].message.content

            tokens_in = response.usage.prompt_tokens if response.usage else 0
            tokens_out = response.usage.completion_tokens if response.usage else 0
            log_llm_call(settings.GROQ_MODEL, tokens_in, tokens_out, latency)

            return result

        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                time.sleep(wait)
            else:
                raise RuntimeError(f"LLM call failed after {max_retries} attempts: {e}")
