from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from .config import load_ai_post_processing_config
from .openrouter import OpenRouterClient, OpenRouterSettings
from .steps import AIPostProcessingStep, GenerateNewsBriefStep, RewriteMainHeadlineStep

Clusters = dict[int, list[Any]]


@dataclass(frozen=True)
class AIPostProcessingConfig:
    enabled: bool = True
    provider: str = "openrouter"
    model: str = "openai/gpt-4o-mini"
    fallback_models: tuple[str, ...] = ()
    healthcheck_enabled: bool = True
    prompts_file: str | None = None


class AIPostProcessingPipeline:
    def __init__(
        self,
        steps: list[AIPostProcessingStep],
        config: AIPostProcessingConfig | None = None,
        generate_brief_step: GenerateNewsBriefStep | None = None,
    ) -> None:
        self.steps = steps
        self.config = config or AIPostProcessingConfig()
        self._generate_brief_step = generate_brief_step

    @property
    def news_brief(self) -> str:
        if self._generate_brief_step is not None:
            return self._generate_brief_step.brief
        return ""

    @classmethod
    def default(
        cls,
        model: str | None = None,
        prompts_file: str | None = None,
    ) -> "AIPostProcessingPipeline":
        loaded_config = load_ai_post_processing_config(prompts_file=prompts_file)
        openrouter_config = loaded_config["openrouter"]

        configured_model = str(openrouter_config["model"])
        fallback_models = tuple(openrouter_config["fallback_models"])
        healthcheck_enabled = bool(openrouter_config["healthcheck_enabled"])
        selected_model = model or configured_model

        if selected_model != configured_model and configured_model not in fallback_models:
            fallback_models = (configured_model, *fallback_models)

        config = AIPostProcessingConfig(
            enabled=True,
            provider="openrouter",
            model=selected_model,
            fallback_models=fallback_models,
            healthcheck_enabled=healthcheck_enabled,
            prompts_file=prompts_file,
        )
        client = OpenRouterClient(
            settings=OpenRouterSettings(
                model=selected_model,
                fallback_models=fallback_models,
                healthcheck_enabled=healthcheck_enabled,
            )
        )
        rewrite_prompt_config = loaded_config["rewrite_main_headline"]
        brief_prompt_config = loaded_config.get("generate_news_brief", {})

        steps: list[AIPostProcessingStep] = [
            RewriteMainHeadlineStep(
                client=client,
                system_prompt_template=rewrite_prompt_config["system_prompt_template"],
                user_prompt_template=rewrite_prompt_config["user_prompt_template"],
            )
        ]

        generate_brief_step: GenerateNewsBriefStep | None = None
        if brief_prompt_config:
            generate_brief_step = GenerateNewsBriefStep(
                client=client,
                system_prompt_template=brief_prompt_config.get(
                    "system_prompt_template",
                    GenerateNewsBriefStep.system_prompt_template,
                ),
                user_prompt_template=brief_prompt_config.get(
                    "user_prompt_template",
                    GenerateNewsBriefStep.user_prompt_template,
                ),
            )
            steps.append(generate_brief_step)

        return cls(steps=steps, config=config, generate_brief_step=generate_brief_step)

    def run(
        self,
        clusters: Clusters,
        news_name: str,
        news_date: date | str,
    ) -> Clusters:
        if not self.config.enabled:
            return clusters

        processed_clusters = clusters
        for step in self.steps:
            processed_clusters = step.run(
                clusters=processed_clusters,
                news_name=news_name,
                news_date=news_date,
            )

        return processed_clusters
