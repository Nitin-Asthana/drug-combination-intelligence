"""Azure OpenAI client using Microsoft Entra ID (no API keys in code).

Auth flow (spec §8):
  1. user runs ``az login``
  2. ``DefaultAzureCredential`` obtains a token for the Cognitive Services scope
  3. the token is supplied to the Azure OpenAI SDK

If Azure is not configured or a token cannot be obtained, ``is_available()``
returns False and the orchestrator falls back to the deterministic demo engine.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import config

logger = logging.getLogger(__name__)


class LLMUnavailable(RuntimeError):
    """Raised when the Azure model cannot be reached."""


class AzureLLM:
    """Thin wrapper around the Azure OpenAI chat completions API."""

    def __init__(self) -> None:
        self._client = None
        self._error: str = ""
        self._init_attempted = False

    # -- lazy initialisation -------------------------------------------------
    def _ensure_client(self) -> None:
        if self._init_attempted:
            return
        self._init_attempted = True

        if not config.azure_openai_configured():
            self._error = "Azure OpenAI endpoint/deployment not configured."
            return
        try:
            from azure.identity import (
                DefaultAzureCredential,
                get_bearer_token_provider,
            )
            from openai import AzureOpenAI

            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, config.AZURE_OPENAI_SCOPE
            )
            self._client = AzureOpenAI(
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
                azure_ad_token_provider=token_provider,
                api_version=config.AZURE_OPENAI_API_VERSION,
            )
        except Exception as exc:  # pragma: no cover - depends on environment
            self._error = f"Azure OpenAI init failed: {exc}"
            self._client = None
            logger.warning(self._error)

    # -- public API ----------------------------------------------------------
    def is_available(self) -> bool:
        self._ensure_client()
        return self._client is not None

    @property
    def status_message(self) -> str:
        self._ensure_client()
        if self._client is not None:
            return "Azure OpenAI connected via Entra ID."
        return self._error or "Azure OpenAI unavailable."

    def complete_json(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.1
    ) -> dict:
        """Return a JSON object from the model. Raises LLMUnavailable on failure."""
        self._ensure_client()
        if self._client is None:
            raise LLMUnavailable(self._error or "Azure OpenAI unavailable.")

        base_kwargs = dict(
            model=config.AZURE_OPENAI_DEPLOYMENT,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        max_tokens = config.AZURE_OPENAI_MAX_TOKENS
        # gpt-5 / o-series accept reasoning_effort; "low" keeps latency down.
        effort = config.AZURE_OPENAI_REASONING_EFFORT
        attempts = []
        if effort:
            attempts.append(
                {**base_kwargs, "reasoning_effort": effort, "max_completion_tokens": max_tokens}
            )
        attempts.append(
            {**base_kwargs, "temperature": temperature, "max_tokens": max_tokens}
        )
        attempts.append(base_kwargs)  # last resort: minimal params

        last_exc: Exception | None = None
        for kwargs in attempts:
            try:
                response = self._client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or "{}"
                return json.loads(content)
            except Exception as exc:  # pragma: no cover - network/runtime dependent
                last_exc = exc
                continue
        raise LLMUnavailable(f"Azure OpenAI call failed: {last_exc}")


# module-level singleton
_llm: Optional[AzureLLM] = None


def get_llm() -> AzureLLM:
    global _llm
    if _llm is None:
        _llm = AzureLLM()
    return _llm
