# x-knowledge

Extract, classify, and semantically search your Twitter likes as a personal knowledge base.

## Overview

x-knowledge ingests your Twitter liked tweets (from a Twitter/X data export), classifies each one into a structured knowledge card using a local LLM via [Ollama](https://ollama.ai), stores them with vector embeddings in SQLite, and provides a semantic search interface to retrieve them by meaning — not just keywords.

## Requirements

- Python 3.12+
- [Ollama](https://ollama.ai) running locally with models:
  - `llama3.1` (or compatible) — for classification
  - `nomic-embed-text` — for embeddings

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install ollama numpy
ollama pull llama3.1
ollama pull nomic-embed-text
```

## Usage

### 1. Classify tweets and build the knowledge base

Place your Twitter likes export as `like.js` in the project root. Then run:

```bash
python knowledge.py
```

This loads `like.js` (or edit the source path in the script), sends each tweet's full text to `llama3.1` for classification, generates an embedding via `nomic-embed-text`, and stores everything in `knowledge.db`.

### Schema

| Column      | Type   | Description                           |
|-------------|--------|---------------------------------------|
| tweet_id    | TEXT   | Twitter status ID (PK)                |
| tweet_url   | TEXT   | Link to the tweet on x.com            |
| raw_text    | TEXT   | Original tweet text                   |
| name        | TEXT   | Short title (LLM-generated, ≤8 words) |
| description | TEXT   | 1–2 sentence summary (≤50 words)      |
| tags        | TEXT   | JSON array of 1–5 tags                |
| embedding   | TEXT   | JSON vector for semantic search       |

### 2. Semantic search

```bash
python knowledge_search.py
```

Type a natural language query (e.g., `"machine learning for beginners"`). Results are ranked by cosine similarity between the query embedding and each stored embedding. Paginated results show relevance score, title, tags, description, and tweet URL.

## How it works

1. **Load** — Parses `like.js` (a Twitter data export file in `window.YTD.like.part0 = [...]` format).
2. **Classify** — For each tweet, sends the full text to `llama3.1` with a structured prompt requesting a name, description, and tags.
3. **Embed** — Generates a vector embedding from the classified metadata + raw text using `nomic-embed-text`.
4. **Store** — Persists everything in a local SQLite database.
5. **Search** — Embeds your query and returns the top results ranked by cosine similarity.

## Project structure

```
knowledge.py         — Main pipeline: classify, embed, store
knowledge_search.py  — Interactive semantic search CLI
like.js              — Twitter likes export (input)
knowledge.db         — SQLite database (generated)
knowledge_backup.db  — Database backup
```
