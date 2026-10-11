"""Server-side OpenAI SDK adapter. Never logs secrets or business payloads."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL, LLM_TIMEOUT_SECONDS

@dataclass(frozen=True)
class ProviderStatus:
    state: str
    message: str
    model: str

class ProviderError(RuntimeError):
    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category

def provider_status() -> ProviderStatus:
    if not LLM_API_KEY:
        return ProviderStatus("missing", "API key is not configured. Analytics-only mode remains available.", LLM_MODEL)
    if not LLM_MODEL:
        return ProviderStatus("missing", "Model name is not configured.", "")
    return ProviderStatus("configured", "Credentials are present; provider connectivity has not yet been checked.", LLM_MODEL)

def _client(api_key: str | None = None, base_url: str | None = None, timeout: float | None = None):
    from openai import OpenAI
    key = LLM_API_KEY if api_key is None else api_key
    if not key:
        raise ProviderError("missing_key", "Set SHOPSENSE_LLM_API_KEY in your local .env file, then restart the app.")
    if not LLM_MODEL:
        raise ProviderError("missing_model", "Set SHOPSENSE_LLM_MODEL in your local .env file, then restart the app.")
    return OpenAI(api_key=key, base_url=base_url or LLM_BASE_URL, timeout=timeout or LLM_TIMEOUT_SECONDS, max_retries=0)

def _classify_error(exc: Exception) -> ProviderError:
    from openai import AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError, NotFoundError, BadRequestError
    if isinstance(exc, AuthenticationError): return ProviderError("invalid_key", "Authentication failed. Check SHOPSENSE_LLM_API_KEY and ensure the key is active.")
    if isinstance(exc, RateLimitError):
        msg = str(exc).lower()
        if "quota" in msg or "billing" in msg or "insufficient_quota" in msg:
            return ProviderError("quota", "The provider reports a quota or billing limit. Check the provider account's billing and usage.")
        return ProviderError("rate_limit", "The provider rate limit was reached. Wait briefly and retry.")
    if isinstance(exc, APITimeoutError): return ProviderError("timeout", "The provider request timed out. Check the network or increase SHOPSENSE_LLM_TIMEOUT_SECONDS modestly.")
    if isinstance(exc, APIConnectionError): return ProviderError("network", "Could not reach the provider. Check network access, proxy settings, and the base URL.")
    if isinstance(exc, NotFoundError): return ProviderError("model", "The provider could not find this model. Check SHOPSENSE_LLM_MODEL and model access.")
    if isinstance(exc, BadRequestError): return ProviderError("request", "The provider rejected the request. Check the configured model and provider/base URL compatibility.")
    return ProviderError("provider", f"Provider request failed ({type(exc).__name__}). Check model, provider settings, and service status; no AI answer was used.")

def test_connection() -> ProviderStatus:
    status = provider_status()
    if status.state == "missing": return status
    try:
        client = _client()
        client.models.retrieve(LLM_MODEL)
        return ProviderStatus("connected", f"Provider connection and model access verified for {LLM_MODEL}.", LLM_MODEL)
    except Exception as exc:
        err = exc if isinstance(exc, ProviderError) else _classify_error(exc)
        return ProviderStatus("error", err.args[0], LLM_MODEL)

def explain_with_llm(question: str, evidence: dict[str, Any]) -> str:
    """Explain already-computed facts; numerical source of truth remains deterministic."""
    import json
    try:
        client = _client()
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You explain small-business analytics concisely. Use only the supplied deterministic evidence. Never invent or alter numbers, dates, currency, or conclusions. If evidence is insufficient, say so. Do not request or infer personal data."},
                {"role": "user", "content": "Question: " + question + "\nDeterministic evidence (JSON): " + json.dumps(evidence, ensure_ascii=False, default=str)},
            ],
            temperature=0,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        content = response.choices[0].message.content
        if not content or not content.strip(): raise ProviderError("empty_response", "The provider returned an empty response. The deterministic result is still available.")
        return content.strip()
    except Exception as exc:
        if isinstance(exc, ProviderError): raise
        raise _classify_error(exc) from None
