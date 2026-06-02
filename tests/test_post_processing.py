from __future__ import annotations

import json
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


UKRAINE_ARTICLE = {
    "title": "Qué dijo Rusia tras el nuevo ataque contra civiles que dejó al menos 18 muertos y más de 100 heridos en Ucrania",
    "body": (
        "Rusia lanzó un nuevo ataque masivo con 656 drones y 73 misiles contra Ucrania: "
        "al menos 13 muertos y decenas de heridos. Mientras edificios residenciales colapsaban, "
        "una maternidad era alcanzada por las explosiones y equipos de rescate trabajaban entre "
        "los escombros, Moscú defendió el ataque masivo lanzado contra Ucrania como una respuesta "
        "legítima a supuestos actos terroristas de Kiev. El Ministerio de Defensa ruso justificó "
        "este martes la ofensiva aérea que dejó al menos 18 muertos entre ellos un niño y más de "
        "un centenar de heridos en distintas regiones ucranianas, al afirmar que los bombardeos "
        "estaban dirigidos exclusivamente contra objetivos militares e infraestructura vinculada "
        "al esfuerzo bélico de Ucrania. La explicación llegó horas después de que Rusia lanzara "
        "uno de los mayores ataques de los últimos meses, con 73 misiles y 656 drones disparados "
        "contra distintas ciudades del país, entre ellas Kiev, Dnipró, Kharkiv, Poltava y "
        "Zaporizhzhia. El Ministerio de Defensa ruso justificó la ofensiva en Ucrania como "
        "respuesta a supuestos actos terroristas de Kiev, alegando impacto solo en objetivos "
        "militares. Durante la noche, en respuesta a los actos terroristas del régimen de Kiev, "
        "las Fuerzas Armadas de la Federación Rusa llevaron a cabo un ataque masivo utilizando "
        "armas de alta precisión de largo alcance aéreas, terrestres y marítimas, señaló el "
        "Ministerio de Defensa ruso en un comunicado. Según Moscú, la ofensiva tuvo como "
        "objetivo instalaciones del complejo militar-industrial ucraniano, infraestructura "
        "energética, redes de transporte utilizadas por el Ejército y aeródromos militares. "
        "El ministerio aseguró además que se emplearon misiles hipersónicos y drones de ataque, "
        "y sostuvo que todos los objetivos fueron alcanzados. En Kiev, los bombardeos "
        "alcanzaron edificios residenciales en varios distritos de la capital, provocando la "
        "muerte de al menos seis personas y dejando decenas de heridos. Uno de los episodios "
        "más graves ocurrió en el distrito de Podil, donde un edificio residencial sufrió un "
        "colapso parcial. Las autoridades locales denunciaron que se utilizó una táctica de "
        "doble golpe, consistente en lanzar un segundo ataque poco después del primero, cuando "
        "los equipos de emergencia ya se encontraban trabajando en la zona. En la región de "
        "Dnipropetrovsk, los ataques dejaron al menos 12 muertos y unos 35 heridos en la "
        "ciudad de Dnipró. Entre las víctimas había un niño cuyo cuerpo fue recuperado entre "
        "los escombros."
    ),
    "source": "Eju.tv",
    "url": "https://eju.tv/...",
    "image_url": "",
    "riesgo": 0.5,
}

UKRAINE_AI_WORDS = (
    "Rusia lanzó un ataque masivo contra Ucrania con 73 misiles y 656 drones "
    "dejando al menos 18 muertos y más de cien heridos. El Ministerio de Defensa "
    "ruso justificó la ofensiva como respuesta a supuestos actos terroristas de Kiev "
    "y aseguró que los bombardeos apuntaron solo a objetivos militares e infraestructura "
    "energética. Las autoridades ucranianas reportaron graves daños en edificios "
    "residenciales en Kiev Dnipró y otras ciudades. En el distrito Podil de la capital "
    "un edificio colapsó parcialmente tras un ataque con táctica de doble golpe que "
    "impactó también a los equipos de rescate. En Dnipró doce personas murieron entre "
    "ellas un niño. Una maternidad en Odesa fue alcanzada pero sin víctimas fatales. "
    "Ucrania afirma que logró interceptar gran parte de los proyectiles. La comunidad "
    "internacional condenó el ataque y pidió una desescalada inmediata del conflicto "
    "que ya lleva más de cuatro años. Los equipos de emergencia continúan trabajando "
    "entre los escombros en busca de más víctimas mientras crece la preocupación por "
    "la escalada bélica. Organizaciones humanitarias denunciaron que los ataques contra "
    "zonas residenciales constituyen violaciones del derecho internacional humanitario. "
    "Rusia por su parte insiste en que solo actúa en defensa propia y que sus ataques "
    "son quirúrgicos contra infraestructura militar. La guerra sigue cobrando víctimas "
    "civiles atrapadas entre ambos bandos."
)

UKRAINE_AI_RESPONSE = json.dumps({
    "title": "Rusia justifica ataque masivo contra Ucrania como respuesta a supuestos actos terroristas de Kiev",
    "body": UKRAINE_AI_WORDS,
})


class UkranianNewsBriefTest(unittest.TestCase):
    def test_rewrite_body_between_150_and_220_words(self) -> None:
        clusters = {0: [dict(UKRAINE_ARTICLE)]}
        step = RewriteMainHeadlineStep(
            client=_ReturningOpenRouterClient(UKRAINE_AI_RESPONSE),
        )

        processed = step.run(clusters=clusters, news_name="Test", news_date="2026-06-02")
        body = processed[0][0]["body"]
        word_count = len(body.split())

        self.assertGreaterEqual(
            word_count, 150,
            f"Body has {word_count} words, expected at least 150. Body: {body[:100]}...",
        )
        self.assertLessEqual(
            word_count, 220,
            f"Body has {word_count} words, expected at most 220. Body: {body[:100]}...",
        )

    def test_rewrite_does_not_exceed_500_words(self) -> None:
        clusters = {0: [dict(UKRAINE_ARTICLE)]}
        long_body = "palabra " * 600
        long_response = f'{{"title": "Título", "body": "{long_body}"}}'
        step = RewriteMainHeadlineStep(
            client=_ReturningOpenRouterClient(long_response),
        )

        processed = step.run(clusters=clusters, news_name="Test", news_date="2026-06-02")
        body = processed[0][0]["body"]
        word_count = len(body.split())

        self.assertLessEqual(
            word_count, 500,
            f"Body has {word_count} words, expected max 500.",
        )


if __name__ == "__main__":
    unittest.main()
