# Setup Guide

This guide gets the project running locally with no cloud keys.

## Requirements

- Python 3.11 or newer
- `uv`
- Docker, only if you want to build the container

## Install

```bash
uv sync --dev
```

## Quality Checks

```bash
make ci
```

This runs:

- Ruff lint checks
- Ruff format check
- mypy type checks
- unit, API, retrieval, ingestion, and golden eval tests

## CLI

Ask a built-in synthetic policy question:

```bash
uv run careshield ask \
  --role nurse \
  --question "Can I send a patient discharge summary to an external vendor?"
```

Analyze an uploaded report-like document through Chroma retrieval:

```bash
uv run careshield analyze-doc \
  --file examples/synthetic-care-report.md \
  --role nurse \
  --question "What must be redacted before vendor sharing?"
```

## API

```bash
make api
```

Open:

```text
http://127.0.0.1:8088/docs
```

## Docker

The Dockerfile uses a Chainguard Python multi-stage build:

- `cgr.dev/chainguard/python:latest-dev` as the builder
- `cgr.dev/chainguard/python:latest` as the minimal runtime
- a virtual environment copied from builder to runtime

Build the container:

```bash
make docker-build
```

Run it:

```bash
docker run --rm -p 8088:8088 careshield-knowledge-assistant
```

Then call:

```bash
curl -s http://127.0.0.1:8088/health | python -m json.tool
```

## Rebuild Example Documents

The repository includes Markdown, PDF, and DOCX synthetic examples. Rebuild
them with:

```bash
make examples
```

The generated examples remain synthetic and public-safe.
