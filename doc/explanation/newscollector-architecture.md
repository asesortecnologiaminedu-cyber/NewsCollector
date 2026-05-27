# Explanation: NewsCollector Architecture

This document explains how NewsCollector is structured and why it is organized this way.

## Audience

Maintainers and contributors who need to understand internals before changing behavior.

## Goal

Understand the data flow, module boundaries, and design decisions behind scraping, clustering, rendering, and AI post-processing.

## High-level flow

`NewsCollector.create()` orchestrates a functional pipeline:

1. **Input resolution** (`configuration.py`)
   - Resolves sources, template, date, and output path.
2. **Scraping** (`scraping.py`)
   - Parses RSS entries and extracts article content via `newspaper`.
3. **Preparation + NLP preprocessing** (`processing.py`)
   - Normalizes records, removes low-quality rows, deduplicates, tokenizes, stems.
4. **Vectorization + clustering** (`processing.py`)
   - TF-IDF vectors + agglomerative clustering.
5. **Post-processing extension point** (`post_processing/`)
   - Optional AI enrichment/rewrite pipeline.
6. **Presentation** (`rendering.py`)
   - Converts clusters to template cards and renders final HTML with Flask templates.

## Why this modular structure

The project was separated into focused modules to reduce coupling:

- `newscollector.py`: orchestration + compatibility facade
- `configuration.py`: argument/file validation and defaults
- `scraping.py`: network ingestion and article extraction
- `processing.py`: text/data transformations and clustering
- `rendering.py`: output materialization
- `post_processing/`: optional, pluggable transformation stages after clustering

This split makes targeted testing and replacement easier (for example, swapping AI steps or render strategy without changing scraping logic).

## Cluster semantics

Clustering currently keeps only groups with at least 2 related articles as "featured clusters".

Implications:

- If no similar stories are found, rendered newsletters can be empty.
- This behavior favors relevance consistency over guaranteed volume.

## AI post-processing design

AI post-processing is intentionally optional and isolated.

- It runs only after clustering, so it does not affect retrieval or clustering boundaries.
- Missing `OPENROUTER_API_KEY` does not stop the main pipeline; rewrite step is skipped with warning.
- Prompt text and OpenRouter model strategy are file-driven (`prompts.json`) for non-code tuning.

### Model healthcheck and fallback

The OpenRouter client uses configured model candidates in priority order.

When healthcheck is enabled:

- It calls OpenRouter `/models`.
- If primary model is unavailable but fallback is available, it switches.
- If healthcheck endpoint fails, it still attempts all configured models at runtime.

This design reduces avoidable failures while preserving forward progress.

## Compatibility and migration posture

The code keeps legacy class names (`Processer`, `Helper`, `Scraper`) and central entrypoints so existing integrations remain usable while internals evolve.

That means maintainers can continue improving internals without forcing immediate API-level migrations.
