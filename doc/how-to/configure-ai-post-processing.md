# How-to: Configure AI Post-processing

Use this guide to configure prompt templates, OpenRouter model selection, model healthcheck, and fallback models.

## Audience

Developers who already run NewsCollector and want to control AI behavior.

## Goal

Make AI post-processing deterministic and configurable from filesystem config.

## 1. Set your OpenRouter API key

Create or update `.env` in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
```

NewsCollector resolves the key in this order:

1. Environment variable `OPENROUTER_API_KEY`
2. `.env` in current working directory
3. `.env` in project root

## 2. Edit the AI config file

Default file:

- `newscollector/post_processing/ai_post_processing/prompts.json`

Example:

```json
{
  "openrouter": {
    "models": [
      "openai/gpt-4o-mini",
      "openai/gpt-4o"
    ],
    "healthcheck_enabled": true
  },
  "rewrite_main_headline": {
    "system_prompt_template": "You rewrite headlines. Keep facts unchanged. Return one sentence only.",
    "user_prompt_template": "Newsletter: {news_name}\nDate: {news_date}\nOriginal title: {original_title}\nBody excerpt: {article_body_excerpt}\nMax length: {max_title_length}"
  }
}
```

### Model config options

You can configure models in two ways:

1. `models` (ordered list)
   - First item is primary model
   - Remaining items are fallback models
2. `model` + `fallback_models`

If both are provided, `models` takes precedence.

## 3. Use a custom config file path (optional)

### Option A: CLI argument

```bash
python newscollector/newscollector.py \
  -s my_sources.json \
  --ai_post_processing true \
  --ai_post_processing_prompts_file /absolute/or/relative/path/prompts.json
```

### Option B: environment variable

```env
NEWSCOLLECTOR_AI_PROMPTS_FILE=/absolute/or/relative/path/prompts.json
```

## 4. Understand model healthcheck and fallback

When `healthcheck_enabled` is `true`:

- NewsCollector checks configured models against OpenRouter `/models`.
- If primary is unavailable but fallback exists, it switches automatically.
- If healthcheck API fails, NewsCollector still tries all configured models at runtime.

If all models fail for a rewrite attempt, that rewrite is skipped, a warning is logged, and the pipeline continues with the original title.

## 5. Verify your configuration

Run with logs enabled (default print logs):

```bash
python newscollector/newscollector.py -s my_sources.json --ai_post_processing true
```

Look for messages such as:

- `Running AI post-processing pipeline.`
- `OpenRouter healthcheck switched model ...`
- `AI post-processing step completed: rewritten cluster headlines.`

If API key is missing, AI rewriting is skipped with a warning.
