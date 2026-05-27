# Reference: NewsCollector API and CLI

This document is a technical reference for public behavior in the current codebase.

## Package exports

`newscollector/__init__.py` exports:

- `NewsCollector`
- `Scraper`
- `Processer`
- `Helper`
- `main`
- `PostProcessingConfig`
- `PostProcessingPipeline`
- `run_post_processing`

## `NewsCollector` class

Location: `newscollector/newscollector.py`

### Constructor

```python
NewsCollector(
    sources: str = "sources.json",
    news_name: str = "Actualización diaria de noticias",
    news_date: date | str | None = None,
    template: str = "newsletter.html",
    output_filename: str = "default",
    auto_open: bool = False,
    return_details: bool = False,
    ai_post_processing: bool = True,
    ai_post_processing_prompts_file: str | None = None,
)
```

### Parameters

- `sources`: JSON path to source definitions.
- `news_name`: Newsletter title rendered in HTML.
- `news_date`: `date`, `YYYY-MM-DD` string, or `None` (today).
- `template`: Template filename; custom `templates/<name>` if present, otherwise package default.
- `output_filename`:
  - `default` -> `newscollector/rendered/newsletter_<date>.html`
  - custom path -> parent directories are created as needed.
- `auto_open`: Open resulting file in default browser.
- `return_details`: Return cluster structures in addition to output path.
- `ai_post_processing`: Enable/disable AI post-processing.
- `ai_post_processing_prompts_file`: Optional prompts/model config file path.

### `create()`

```python
create() -> str | tuple[str, dict[int, list[Any]], dict[int, list[Any]]]
```

Returns:

- `str` output path when `return_details=False`
- `(output_path, clusters, featured_clusters)` when `return_details=True`

Pipeline sequence:

1. Scrape RSS sources
2. Convert to DataFrame
3. Clean/filter articles
4. Compute TF-IDF
5. Cluster articles
6. Run post-processing (AI optional)
7. Render HTML

## CLI reference

Entry point: `python newscollector/newscollector.py`

### Arguments

- `-s`, `--sources` (str)
- `-n`, `--news_name` (str)
- `-d`, `--news_date` (`YYYY-MM-DD` str)
- `-t`, `--template` (str)
- `-o`, `--output_filename` (str)
- `-r`, `--return_details` (bool-like value)
- `-a`, `--auto_open` (bool-like value)
- `--ai_post_processing` (bool-like value)
- `--ai_post_processing_prompts_file` (str)

Accepted bool values:

- truthy: `1`, `true`, `t`, `yes`, `y`, `on`
- falsy: `0`, `false`, `f`, `no`, `n`, `off`

## Source file format

`sources.json` format:

```json
{
  "Source Name": {
    "rss": [
      "https://example.com/feed"
    ]
  }
}
```

## AI post-processing config file format

Default path:

- `newscollector/post_processing/ai_post_processing/prompts.json`

### OpenRouter section

```json
{
  "openrouter": {
    "models": ["openai/gpt-4o-mini", "openai/gpt-4o"],
    "healthcheck_enabled": true
  }
}
```

Alternative model schema is also accepted:

```json
{
  "openrouter": {
    "model": "openai/gpt-4o-mini",
    "fallback_models": ["openai/gpt-4o"],
    "healthcheck_enabled": true
  }
}
```

### Prompt template section

```json
{
  "rewrite_main_headline": {
    "system_prompt_template": "...",
    "user_prompt_template": "..."
  }
}
```

Supported template placeholders:

- `{news_name}`
- `{news_date}`
- `{original_title}`
- `{article_body_excerpt}`
- `{max_title_length}`

## Environment variables

- `OPENROUTER_API_KEY`: API key used by OpenRouter client.
- `NEWSCOLLECTOR_AI_PROMPTS_FILE`: Optional prompt/model config file path.
