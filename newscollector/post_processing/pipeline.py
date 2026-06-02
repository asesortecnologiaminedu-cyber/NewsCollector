from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

try:
    from ..logging_utils import log_info
    from .ai_post_processing import AIPostProcessingPipeline
except ImportError:  # pragma: no cover - direct script execution support
    from logging_utils import log_info
    from post_processing.ai_post_processing import AIPostProcessingPipeline

Clusters = dict[int, list[Any]]


@dataclass(frozen=True)
class PostProcessingConfig:
    enable_ai_post_processing: bool = True
    openrouter_model: str | None = None
    ai_prompts_file: str | None = None


@dataclass(frozen=True)
class PostProcessingResult:
    clusters: Clusters
    news_brief: str = ""


class PostProcessingPipeline:
    def __init__(
        self,
        config: PostProcessingConfig | None = None,
        ai_pipeline: AIPostProcessingPipeline | None = None,
    ) -> None:
        self.config = config or PostProcessingConfig()
        self.ai_pipeline = ai_pipeline or AIPostProcessingPipeline.default(
            model=self.config.openrouter_model,
            prompts_file=self.config.ai_prompts_file,
        )

    @property
    def news_brief(self) -> str:
        return self.ai_pipeline.news_brief

    def run(
        self,
        clusters: Clusters,
        news_name: str,
        news_date: date | str,
    ) -> PostProcessingResult:
        if not clusters:
            return PostProcessingResult(clusters=clusters)

        processed_clusters = clusters
        if self.config.enable_ai_post_processing:
            log_info("Running AI post-processing pipeline.")
            processed_clusters = self.ai_pipeline.run(
                clusters=processed_clusters,
                news_name=news_name,
                news_date=news_date,
            )

        return PostProcessingResult(
            clusters=processed_clusters,
            news_brief=self.news_brief,
        )


def run_post_processing(
    clusters: Clusters,
    news_name: str,
    news_date: date | str,
    enable_ai_post_processing: bool = True,
    openrouter_model: str | None = None,
    ai_prompts_file: str | None = None,
) -> PostProcessingResult:
    pipeline = PostProcessingPipeline(
        config=PostProcessingConfig(
            enable_ai_post_processing=enable_ai_post_processing,
            openrouter_model=openrouter_model,
            ai_prompts_file=ai_prompts_file,
        )
    )
    return pipeline.run(clusters=clusters, news_name=news_name, news_date=news_date)
