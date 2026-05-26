from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

try:
    from ...logging_utils import log_info, log_warn
except ImportError:  # pragma: no cover - direct script execution support
    from logging_utils import log_info, log_warn

from .config import load_openrouter_api_key


@dataclass(frozen=True)
class OpenRouterSettings:
    api_key: str | None = None
    model: str = "openai/gpt-4o-mini"
    fallback_models: tuple[str, ...] = ()
    healthcheck_enabled: bool = True
    base_url: str = "https://openrouter.ai/api/v1"
    app_name: str = "NewsCollector"
    timeout_seconds: int = 45


class OpenRouterClient:
    def __init__(self, settings: OpenRouterSettings | None = None) -> None:
        self.settings = settings or OpenRouterSettings()
        self.api_key = self.settings.api_key or load_openrouter_api_key()
        self._active_model = self.settings.model
        self._healthcheck_results: dict[str, bool] | None = None

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def configured_models(self) -> list[str]:
        candidate_models = [self.settings.model, *self.settings.fallback_models]
        unique_models: list[str] = []
        for model in candidate_models:
            if model and model not in unique_models:
                unique_models.append(model)
        return unique_models

    def healthcheck_models(self, force_refresh: bool = False) -> dict[str, bool]:
        if self._healthcheck_results is not None and not force_refresh:
            return self._healthcheck_results.copy()

        models = self.configured_models()
        if not models:
            self._healthcheck_results = {}
            return {}

        if not self.settings.healthcheck_enabled:
            self._healthcheck_results = {model: True for model in models}
            return self._healthcheck_results.copy()

        if not self.api_key:
            self._healthcheck_results = {model: False for model in models}
            return self._healthcheck_results.copy()

        try:
            available_models = self._fetch_available_models()
        except Exception as exc:
            log_warn(f"OpenRouter model healthcheck failed: {exc}. Falling back to runtime attempts.")
            self._healthcheck_results = {model: True for model in models}
            return self._healthcheck_results.copy()

        self._healthcheck_results = {model: model in available_models for model in models}

        first_available_model = next(
            (model for model, is_available in self._healthcheck_results.items() if is_available),
            None,
        )
        if first_available_model:
            if first_available_model != self._active_model:
                log_info(
                    f'OpenRouter healthcheck switched model from "{self._active_model}" '
                    f'to fallback "{first_available_model}".'
                )
            self._active_model = first_available_model
        else:
            log_warn(
                "OpenRouter healthcheck found no configured models available. "
                "Runtime fallback attempts will still be performed."
            )

        return self._healthcheck_results.copy()

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 160,
        temperature: float = 0.2,
    ) -> str:
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is missing. Set it in your environment or .env file."
            )

        healthcheck_results = self.healthcheck_models()
        candidate_models = self._ordered_models()
        errors: list[tuple[str, Exception]] = []
        attempted_models = 0

        for model in candidate_models:
            if not healthcheck_results.get(model, True):
                continue

            attempted_models += 1
            try:
                response_text = self._generate_text_with_model(
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                self._active_model = model
                return response_text
            except Exception as exc:
                errors.append((model, exc))

        if attempted_models == 0:
            for model in candidate_models:
                try:
                    response_text = self._generate_text_with_model(
                        model=model,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    self._active_model = model
                    return response_text
                except Exception as exc:
                    errors.append((model, exc))

        error_details = "; ".join(f"{model}: {error}" for model, error in errors)
        raise RuntimeError(
            "OpenRouter request failed for all configured models. "
            f"Tried models: {candidate_models}. Errors: {error_details}"
        )

    def _ordered_models(self) -> list[str]:
        configured_models = self.configured_models()
        if not configured_models:
            return []

        if self._active_model not in configured_models:
            return configured_models

        return [self._active_model, *[m for m in configured_models if m != self._active_model]]

    def _fetch_available_models(self) -> set[str]:
        response = requests.get(
            f"{self.settings.base_url}/models",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Title": self.settings.app_name,
            },
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()

        response_payload: dict[str, Any] = response.json()
        model_entries = response_payload.get("data", [])
        if not isinstance(model_entries, list):
            return set()

        available_models: set[str] = set()
        for model_entry in model_entries:
            if not isinstance(model_entry, dict):
                continue

            model_id = model_entry.get("id")
            if isinstance(model_id, str) and model_id.strip():
                available_models.add(model_id.strip())

        return available_models

    def _generate_text_with_model(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:

        request_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = requests.post(
            f"{self.settings.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Title": self.settings.app_name,
            },
            json=request_payload,
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()

        response_payload: dict[str, Any] = response.json()
        choices = response_payload.get("choices", [])
        if not choices:
            raise RuntimeError("OpenRouter returned an empty choices list.")

        message_content = choices[0].get("message", {}).get("content", "")
        cleaned_content = str(message_content).strip()
        if not cleaned_content:
            raise RuntimeError("OpenRouter response did not include text content.")

        return cleaned_content
