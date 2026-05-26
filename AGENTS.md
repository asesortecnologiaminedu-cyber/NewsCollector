# NewsCollector Agent Instructions

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Default sources: `newscollector/sources.json`
- Default template: `newscollector/templates/newsletter.html`
- Output directory: `newscollector/rendered/` (created automatically)

## Usage
### Programmatic
```python
from newscollector import NewsCollector
newsletter = NewsCollector(sources="sources.json", news_name="My News")
output = newsletter.create()  # Returns path to HTML file
```

### CLI
```bash
python newscollector/newscollector.py -s sources.json -n "My News" -o output.html
```

## Important Notes
- Output filename 'default' creates `newsletter_YYYY-MM-DD.html` in rendered/
- Set `auto_open=True` to open newsletter in browser after generation
- Set `return_details=True` to get clusters data along with output path
- Requires internet connection to scrape RSS feeds
- Processing time depends on number of sources and articles
- **CLI Parameter Order Bug**: The CLI has a bug where `--return_details` and `--auto_open` are swapped. When using CLI, specify `--auto_open` before `--return_details` to get the expected behavior, or use keyword arguments in programmatic usage.

## Development
- Main logic: `newscollector/newscollector.py`
- Helper functions in `Helper`, `Scraper`, `Processer` classes
- Templates use Flask templating system