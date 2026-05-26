# Tutorial: Create Your First Newsletter

This tutorial guides you from zero to a generated HTML newsletter.

## Audience

Developers new to this project who want a successful first run.

## Goal

Generate one newsletter HTML file from RSS feeds and understand where the output is stored.

## Prerequisites

- Python 3.10+
- Internet access (RSS scraping and article extraction require network access)
- Project checked out locally

## 1. Install dependencies

From the project root:

```bash
pip install -r requirements.txt
```

If NLTK tokenizer data is missing on first run, install it:

```bash
python -m nltk.downloader punkt punkt_tab
```

## 2. Create a minimal source file

Create `my_sources.json`:

```json
{
  "BBC": {
    "rss": [
      "https://feeds.bbci.co.uk/news/rss.xml"
    ]
  }
}
```

## 3. Run from Python

```python
from newscollector import NewsCollector

collector = NewsCollector(
    sources="my_sources.json",
    news_name="My Daily Brief",
    output_filename="default",
    auto_open=False,
    return_details=False,
    ai_post_processing=True,
)

output_path = collector.create()
print(output_path)
```

Expected result:

- The method returns the generated HTML path.
- With `output_filename="default"`, output is written to:
  - `newscollector/rendered/newsletter_YYYY-MM-DD.html`

## 4. Run from CLI

Equivalent CLI run:

```bash
python newscollector/newscollector.py \
  -s my_sources.json \
  -n "My Daily Brief" \
  -o default \
  --ai_post_processing true
```

## 5. Verify the output

- Open the printed output path in a browser.
- Confirm cards are rendered when clustered stories are found.
- If you get an empty newsletter, check logs:
  - scraping counts
  - cleaning counts
  - clustering summary

## What you learned

- How to run NewsCollector from Python and CLI
- Where output files are written
- What to inspect when output is empty

## Next step

Use `doc/how-to/configure-ai-post-processing.md` to customize AI prompts, model selection, healthcheck, and fallback models.
