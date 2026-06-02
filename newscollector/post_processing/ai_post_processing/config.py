from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_PROMPT_CONFIG_PATH = Path(__file__).with_name("prompts.json")

DEFAULT_PROMPT_CONFIG: dict[str, dict[str, str]] = {
    "rewrite_main_headline": {
        "system_prompt_template": (
            "Eres un asistente de resumen de noticias. Reescribes titulares y generas "
            "resúmenes breves en español. Conserva los hechos clave sin inventar "
            "información. Devuelve solo JSON válido sin markdown ni texto adicional."
        ),
        "user_prompt_template": (
            "Resume la siguiente noticia en español.\n\n"
            "Requisitos:\n"
            "1. Reescribe el titular preservando los hechos clave. "
            "Máximo {max_title_length} caracteres.\n"
            "2. Genera un cuerpo de resumen de aproximadamente 200 caracteres "
            "con los datos esenciales.\n"
            "3. No inventes hechos, nombres, fechas ni conclusiones.\n"
            "4. Devuelve solo JSON con exactamente estos dos campos: title y body.\n\n"
            "Entrada:\n"
            "{article_payload_json}\n\n"
            "Formato de salida:\n"
            "{{\n"
            "  \"title\": \"titular reescrito aquí\",\n"
            "  \"body\": \"resumen conciso de unos 200 caracteres aquí\"\n"
            "}}"
        ),
    },
    "generate_news_brief": {
        "system_prompt_template": (
            "Eres un periodista. Escribes solo el texto del resumen en español, "
            "sin títulos, sin encabezados, sin frases introductorias, "
            "sin repetir instrucciones."
        ),
        "user_prompt_template": (
            "Resume en ~200 palabras las noticias siguientes, "
            "ordenadas por importancia. Escribe solo el texto informativo, "
            "sin introducción ni títulos.\n\n"
            "{clusters_json}"
        ),
    },
}

DEFAULT_OPENROUTER_CONFIG: dict[str, Any] = {
    "model": "openai/gpt-4o-mini",
    "fallback_models": ["openai/gpt-4o"],
    "healthcheck_enabled": True,
}


def load_openrouter_api_key(env_file: str | Path | None = None) -> str | None:
    env_api_key = os.getenv("OPENROUTER_API_KEY")
    if env_api_key:
        return env_api_key.strip()

    env_file_candidates = _env_candidates(env_file)
    for file_path in env_file_candidates:
        file_api_key = _read_env_value(file_path, "OPENROUTER_API_KEY")
        if file_api_key:
            return file_api_key

    return None


def load_ai_post_processing_config(prompts_file: str | Path | None = None) -> dict[str, Any]:
    config_path = _resolve_prompt_config_path(prompts_file)

    if not config_path.exists() or not config_path.is_file():
        return _default_ai_post_processing_config()

    try:
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return _default_ai_post_processing_config()

    if not isinstance(raw_config, dict):
        return _default_ai_post_processing_config()

    normalized_config = _default_ai_post_processing_config()
    normalized_config["openrouter"] = _normalize_openrouter_config(raw_config)
    normalized_config.update(_normalize_prompt_config(raw_config))
    return normalized_config


def load_ai_prompt_config(prompts_file: str | Path | None = None) -> dict[str, dict[str, str]]:
    full_config = load_ai_post_processing_config(prompts_file=prompts_file)
    return {
        step_name: prompt_templates
        for step_name, prompt_templates in full_config.items()
        if step_name != "openrouter"
    }


def _resolve_prompt_config_path(prompts_file: str | Path | None) -> Path:
    if prompts_file is not None:
        return Path(prompts_file)

    env_prompts_file = os.getenv("NEWSCOLLECTOR_AI_PROMPTS_FILE")
    if env_prompts_file:
        return Path(env_prompts_file)

    return DEFAULT_PROMPT_CONFIG_PATH


def _default_ai_post_processing_config() -> dict[str, Any]:
    prompt_defaults = {
        step_name: prompt_templates.copy()
        for step_name, prompt_templates in DEFAULT_PROMPT_CONFIG.items()
    }
    return {
        "openrouter": _default_openrouter_config(),
        **prompt_defaults,
    }


def _default_openrouter_config() -> dict[str, Any]:
    return {
        "model": str(DEFAULT_OPENROUTER_CONFIG["model"]),
        "fallback_models": list(DEFAULT_OPENROUTER_CONFIG["fallback_models"]),
        "healthcheck_enabled": bool(DEFAULT_OPENROUTER_CONFIG["healthcheck_enabled"]),
    }


def _normalize_openrouter_config(raw_config: dict[str, Any]) -> dict[str, Any]:
    normalized_openrouter = _default_openrouter_config()
    raw_openrouter = raw_config.get("openrouter")

    if not isinstance(raw_openrouter, dict):
        return normalized_openrouter

    configured_models = _normalize_models_list(raw_openrouter.get("models"))
    if configured_models:
        normalized_openrouter["model"] = configured_models[0]
        normalized_openrouter["fallback_models"] = configured_models[1:]
    else:
        model = raw_openrouter.get("model")
        if isinstance(model, str) and model.strip():
            normalized_openrouter["model"] = model.strip()

        fallback_models = _normalize_models_list(raw_openrouter.get("fallback_models"))
        if fallback_models:
            normalized_openrouter["fallback_models"] = fallback_models

    healthcheck_enabled = raw_openrouter.get("healthcheck_enabled")
    if isinstance(healthcheck_enabled, bool):
        normalized_openrouter["healthcheck_enabled"] = healthcheck_enabled

    if normalized_openrouter["model"] in normalized_openrouter["fallback_models"]:
        normalized_openrouter["fallback_models"] = [
            model
            for model in normalized_openrouter["fallback_models"]
            if model != normalized_openrouter["model"]
        ]

    return normalized_openrouter


def _normalize_models_list(raw_models: Any) -> list[str]:
    if not isinstance(raw_models, list):
        return []

    normalized_models: list[str] = []
    for model in raw_models:
        if not isinstance(model, str):
            continue

        cleaned_model = model.strip()
        if cleaned_model and cleaned_model not in normalized_models:
            normalized_models.append(cleaned_model)

    return normalized_models


def _normalize_prompt_config(raw_config: Any) -> dict[str, dict[str, str]]:
    if not isinstance(raw_config, dict):
        return {
            step_name: prompt_templates.copy()
            for step_name, prompt_templates in DEFAULT_PROMPT_CONFIG.items()
        }

    merged_config = {
        step_name: prompt_templates.copy()
        for step_name, prompt_templates in DEFAULT_PROMPT_CONFIG.items()
    }

    for step_name, step_config in raw_config.items():
        if not isinstance(step_name, str) or not isinstance(step_config, dict):
            continue

        default_step = merged_config.get(step_name, {}).copy()
        for template_key in ("system_prompt_template", "user_prompt_template"):
            template_value = step_config.get(template_key)
            if isinstance(template_value, str) and template_value.strip():
                default_step[template_key] = template_value

        if default_step:
            merged_config[step_name] = default_step

    return merged_config


def _env_candidates(env_file: str | Path | None) -> list[Path]:
    if env_file is not None:
        return [Path(env_file)]

    package_root = Path(__file__).resolve().parents[3]
    return [Path.cwd() / ".env", package_root / ".env"]


def _read_env_value(file_path: Path, key: str) -> str | None:
    if not file_path.exists() or not file_path.is_file():
        return None

    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        line_key, line_value = line.split("=", 1)
        if line_key.strip() != key:
            continue

        cleaned_value = line_value.strip().strip('"').strip("'")
        return cleaned_value or None

    return None
