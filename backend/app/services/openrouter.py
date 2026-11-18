"""OpenRouter API client with retry, timeout and error handling."""

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are EstateIQ, a real estate intelligence assistant. Your knowledge comes EXCLUSIVELY from the context provided below.

STRICT RULES:
1. Only state facts that appear word-for-word in the provided context. Do not infer, assume, or add details not present.
2. If a fact is not in the context, say: "I could not find verified information about this in the collected data."
3. NEVER mention project names, prices, locations, or people that are not explicitly in the provided context.
4. Always cite the source URL when you use information from a source.
5. Keep answers factual, concise, and professional.
6. Do not add qualifiers like "based on my training data" — your only knowledge source is the context below."""


class OpenRouterError(Exception):
    pass


class OpenRouterClient:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.openrouter_base_url
        self.api_key = self.settings.openrouter_api_key
        self.model = self.settings.openrouter_model
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    def _build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://estateiq.app",
            "X-Title": "EstateIQ Real Estate Assistant",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        user_message: str,
        context_chunks: list[dict],
        conversation_history: list[dict] = None,
    ) -> dict:
        """
        Send a message to OpenRouter with RAG context.
        Returns dict with 'answer', 'model', 'tokens'.
        """
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not configured. "
                "Please add your OpenRouter API key to the .env file and restart the server."
            )

        # Build context block from retrieved chunks
        if context_chunks:
            context_parts = []
            for i, chunk in enumerate(context_chunks, 1):
                context_parts.append(
                    f"[Source {i}] {chunk['title']}\n"
                    f"URL: {chunk['source_url']}\n"
                    f"Content: {chunk['content']}"
                )
            context_text = "\n\n---\n\n".join(context_parts)
            context_block = (
                f"\n\nRELEVANT CONTEXT FROM COLLECTED DATA:\n\n{context_text}\n\n"
                f"Answer the question using the above context. "
                f"Always cite source URLs when referencing specific information."
            )
        else:
            context_block = (
                "\n\nNo relevant context was found in the collected data. "
                "Inform the user that the information could not be verified from "
                "DarGlobal or Wasalt sources."
            )

        messages = [{"role": "system", "content": SYSTEM_PROMPT + context_block}]

        # Add conversation history (last 6 exchanges max)
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._build_headers(),
                    json=payload,
                )

                # Handle specific HTTP error codes before raise_for_status
                if response.status_code == 401:
                    raise OpenRouterError(
                        "Invalid OpenRouter API key (401). "
                        "Please check your OPENROUTER_API_KEY in the .env file."
                    )
                if response.status_code == 404:
                    raise OpenRouterError(
                        "OpenRouter API endpoint not found (404). "
                        "Check that OPENROUTER_BASE_URL is correct: "
                        "https://openrouter.ai/api/v1"
                    )
                if response.status_code == 429:
                    raise OpenRouterError(
                        "OpenRouter rate limit reached (429). "
                        "Please wait a moment and try again."
                    )
                if response.status_code == 402:
                    raise OpenRouterError(
                        "OpenRouter account credit limit reached (402). "
                        "Please check your OpenRouter account balance."
                    )
                if response.status_code >= 500:
                    raise OpenRouterError(
                        f"OpenRouter service error ({response.status_code}). "
                        "Please try again in a moment."
                    )

                response.raise_for_status()
                data = response.json()

                answer = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )

                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                model_used = data.get("model", self.model)

                return {
                    "answer": answer or "I was unable to generate a response. Please try again.",
                    "model": model_used,
                    "tokens": tokens,
                }

            except httpx.TimeoutException:
                raise OpenRouterError(
                    "The AI service timed out. Please try again in a moment."
                )
            except httpx.NetworkError as e:
                raise OpenRouterError(
                    f"Network error connecting to OpenRouter: {e}"
                )
            except httpx.HTTPStatusError as e:
                raise OpenRouterError(
                    f"OpenRouter HTTP error {e.response.status_code}. "
                    "Please check your API key and try again."
                )
