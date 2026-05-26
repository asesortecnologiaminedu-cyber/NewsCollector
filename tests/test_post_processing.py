from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from newscollector.post_processing import run_post_processing
from newscollector.post_processing.ai_post_processing.config import (
    load_ai_post_processing_config,
    load_ai_prompt_config,
    load_openrouter_api_key,
)
from newscollector.post_processing.ai_post_processing.openrouter import (
    OpenRouterClient,
    OpenRouterSettings,
)
from newscollector.post_processing.ai_post_processing.pipeline import AIPostProcessingPipeline
from newscollector.post_processing.ai_post_processing.steps import RewriteMainHeadlineStep


class _FakeOpenRouterClient:
    def __init__(self, configured: bool = True) -> None:
        self._configured = configured

    def is_configured(self) -> bool:
        return self._configured

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 160,
        temperature: float = 0.2,
    ) -> str:
        return "Rewritten headline"


class _CapturingOpenRouterClient:
    def __init__(self) -> None:
        self.system_prompt = ""
        self.user_prompt = ""

    def is_configured(self) -> bool:
        return True

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 160,
        temperature: float = 0.2,
    ) -> str:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return "Rewritten headline"


class _ReturningOpenRouterClient:
    def __init__(self, output: str) -> None:
        self.output = output

    def is_configured(self) -> bool:
        return True

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 160,
        temperature: float = 0.2,
    ) -> str:
        return self.output


class PostProcessingTests(unittest.TestCase):
    def test_load_openrouter_api_key_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("OPENROUTER_API_KEY=test-key\n", encoding="utf-8")

            with patch.dict("os.environ", {}, clear=True):
                api_key = load_openrouter_api_key(env_file=env_file)

            self.assertEqual(api_key, "test-key")

    def test_run_post_processing_returns_input_when_ai_disabled(self) -> None:
        clusters = {
            0: [
                {
                    "title": "Original headline",
                    "body": "Body",
                    "source": "Source",
                    "url": "https://example.com",
                    "image_url": "https://example.com/image.png",
                }
            ]
        }

        processed_clusters = run_post_processing(
            clusters=clusters,
            news_name="News",
            news_date="2026-05-26",
            enable_ai_post_processing=False,
        )

        self.assertEqual(processed_clusters[0][0]["title"], "Original headline")

    def test_load_ai_prompt_config_reads_filesystem_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompts_file = Path(temp_dir) / "prompts.json"
            prompts_file.write_text(
                (
                    "{"
                    '"rewrite_main_headline": {'
                    '"system_prompt_template": "System {news_name}", '
                    '"user_prompt_template": "Title {original_title}"'
                    "}"
                    "}"
                ),
                encoding="utf-8",
            )

            prompts = load_ai_prompt_config(prompts_file=prompts_file)

        self.assertEqual(
            prompts["rewrite_main_headline"]["system_prompt_template"],
            "System {news_name}",
        )
        self.assertEqual(
            prompts["rewrite_main_headline"]["user_prompt_template"],
            "Title {original_title}",
        )

    def test_load_ai_post_processing_config_reads_models_and_fallbacks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompts_file = Path(temp_dir) / "prompts.json"
            prompts_file.write_text(
                (
                    "{"
                    '"openrouter": {'
                    '"models": ["meta-llama/llama-3.1-8b-instruct", "openai/gpt-4o-mini"], '
                    '"healthcheck_enabled": false'
                    "},"
                    '"rewrite_main_headline": {'
                    '"system_prompt_template": "System", '
                    '"user_prompt_template": "User"'
                    "}"
                    "}"
                ),
                encoding="utf-8",
            )

            config = load_ai_post_processing_config(prompts_file=prompts_file)

        self.assertEqual(
            config["openrouter"]["model"],
            "meta-llama/llama-3.1-8b-instruct",
        )
        self.assertEqual(
            config["openrouter"]["fallback_models"],
            ["openai/gpt-4o-mini"],
        )
        self.assertFalse(config["openrouter"]["healthcheck_enabled"])

    def test_openrouter_healthcheck_switches_to_fallback_model(self) -> None:
        settings = OpenRouterSettings(
            api_key="test-key",
            model="primary/model",
            fallback_models=("fallback/model",),
            healthcheck_enabled=True,
        )
        client = OpenRouterClient(settings=settings)

        models_response = Mock()
        models_response.raise_for_status = Mock()
        models_response.json.return_value = {
            "data": [
                {"id": "fallback/model"},
            ]
        }

        completion_response = Mock()
        completion_response.raise_for_status = Mock()
        completion_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "ok",
                    }
                }
            ]
        }

        with patch(
            "newscollector.post_processing.ai_post_processing.openrouter.requests.get",
            return_value=models_response,
        ), patch(
            "newscollector.post_processing.ai_post_processing.openrouter.requests.post",
            return_value=completion_response,
        ) as post_mock:
            generated_text = client.generate_text(system_prompt="system", user_prompt="user")

        self.assertEqual(generated_text, "ok")
        sent_payload = post_mock.call_args.kwargs["json"]
        self.assertEqual(sent_payload["model"], "fallback/model")

    def test_ai_pipeline_step_rewrites_title(self) -> None:
        clusters = {
            0: [
                {
                    "title": "Original headline",
                    "body": "Long body text",
                    "source": "Source",
                    "url": "https://example.com",
                    "image_url": "https://example.com/image.png",
                }
            ]
        }

        pipeline = AIPostProcessingPipeline(
            steps=[
                RewriteMainHeadlineStep(
                    client=_FakeOpenRouterClient(configured=True),
                    system_prompt_template="System",
                    user_prompt_template="Title {original_title}",
                )
            ]
        )
        processed_clusters = pipeline.run(
            clusters=clusters,
            news_name="Daily Brief",
            news_date="2026-05-26",
        )

        self.assertEqual(processed_clusters[0][0]["title"], "Rewritten headline")

    def test_ai_pipeline_skips_when_no_api_key(self) -> None:
        clusters = {
            0: [
                {
                    "title": "Original headline",
                    "body": "Long body text",
                    "source": "Source",
                    "url": "https://example.com",
                    "image_url": "https://example.com/image.png",
                }
            ]
        }

        pipeline = AIPostProcessingPipeline(
            steps=[
                RewriteMainHeadlineStep(
                    client=_FakeOpenRouterClient(configured=False),
                    system_prompt_template="System",
                    user_prompt_template="Title {original_title}",
                )
            ]
        )
        processed_clusters = pipeline.run(
            clusters=clusters,
            news_name="Daily Brief",
            news_date="2026-05-26",
        )

        self.assertEqual(processed_clusters[0][0]["title"], "Original headline")

    def test_step_formats_prompts_from_template_values(self) -> None:
        clusters = {
            0: [
                {
                    "title": "Original headline",
                    "body": "Body text here",
                    "source": "Source",
                    "url": "https://example.com",
                    "image_url": "https://example.com/image.png",
                }
            ]
        }
        client = _CapturingOpenRouterClient()
        step = RewriteMainHeadlineStep(
            client=client,
            system_prompt_template="System for {news_name}",
            user_prompt_template="Headline: {original_title} | Date: {news_date}",
        )

        step.run(clusters=clusters, news_name="Daily Brief", news_date="2026-05-26")

        self.assertIn("Daily Brief", client.system_prompt)
        self.assertIn("Original headline", client.user_prompt)

    def test_step_default_prompt_escapes_special_characters(self) -> None:
        clusters = {
            0: [
                {
                    "title": 'He said "hola"\nThen {ignored}',
                    "body": "Body with quote: \"value\" and newline\nMax length: 5",
                    "source": "Source",
                    "url": "https://example.com",
                    "image_url": "https://example.com/image.png",
                }
            ]
        }
        client = _CapturingOpenRouterClient()
        step = RewriteMainHeadlineStep(client=client)

        step.run(clusters=clusters, news_name="Daily Brief", news_date="2026-05-26")

        self.assertIn("JSON payload:", client.user_prompt)
        self.assertIn('"original_title": "He said \\\"hola\\\"\\nThen {ignored}"', client.user_prompt)
        self.assertIn('"article_body_excerpt": "Body with quote: \\\"value\\\" and newline\\nMax length: 5"', client.user_prompt)

    def test_step_rejects_prompt_echo_output(self) -> None:
        clusters = {
            0: [
                {
                    "title": "Aprehenden a exdirector de la ABC por inve",
                    "body": "Body",
                    "source": "Source",
                    "url": "https://example.com",
                    "image_url": "https://example.com/image.png",
                }
            ]
        }
        step = RewriteMainHeadlineStep(
            client=_ReturningOpenRouterClient(
                'We need to rewrite the headline, keep core facts unchanged. Original title: "Aprehenden a exdirector de la ABC por inve"'
            )
        )

        processed_clusters = step.run(
            clusters=clusters,
            news_name="Daily Brief",
            news_date="2026-05-26",
        )

        self.assertEqual(
            processed_clusters[0][0]["title"],
            "Aprehenden a exdirector de la ABC por inve",
        )

    def test_step_rejects_prompt_echo_output_with_quoted_original_title(self) -> None:
        clusters = {
            0: [
                {
                    "title": "Rodrigo Paz: 'Evo Morales va a acabar en la justicia'",
                    "body": "Body",
                    "source": "Source",
                    "url": "https://example.com",
                    "image_url": "https://example.com/image.png",
                }
            ]
        }
        step = RewriteMainHeadlineStep(
            client=_ReturningOpenRouterClient(
                'We need to rewrite one concise headline from the JSON payload. The original title: "Rodrigo Paz: ‘Evo Morales va a acabar en la justicia’"'
            )
        )

        processed_clusters = step.run(
            clusters=clusters,
            news_name="Daily Brief",
            news_date="2026-05-26",
        )

        self.assertEqual(
            processed_clusters[0][0]["title"],
            "Rodrigo Paz: 'Evo Morales va a acabar en la justicia'",
        )

    def test_step_accepts_legitimate_headline_with_quotes(self) -> None:
        clusters = {
            0: [
                {
                    "title": "Rodrigo Paz: 'Evo Morales va a acabar en la justicia'",
                    "body": "Body",
                    "source": "Source",
                    "url": "https://example.com",
                    "image_url": "https://example.com/image.png",
                }
            ]
        }
        step = RewriteMainHeadlineStep(
            client=_ReturningOpenRouterClient(
                'Rodrigo Paz afirma: "Evo Morales va a acabar en la justicia"'
            )
        )

        processed_clusters = step.run(
            clusters=clusters,
            news_name="Daily Brief",
            news_date="2026-05-26",
        )

        self.assertEqual(
            processed_clusters[0][0]["title"],
            'Rodrigo Paz afirma: "Evo Morales va a acabar en la justicia"',
        )


if __name__ == "__main__":
    unittest.main()
