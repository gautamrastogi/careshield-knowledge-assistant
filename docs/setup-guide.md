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

## AWS Bedrock Gateway Shape

The default local path uses `MockModelGateway`, so no AWS credentials are
required. The project also includes a `BedrockConverseGateway` adapter to show
how the same application boundary maps to AWS Bedrock Runtime.

Minimal Python shape:

```python
from careshield import contracts, pipeline

gateway = pipeline.gateway.BedrockConverseGateway(
    config=contracts.schema.BedrockGatewayConfig(
        region_name="eu-central-1",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        guardrail_identifier="your-guardrail-id",
        guardrail_version="1",
    )
)
```

The adapter uses `boto3.client("bedrock-runtime").converse(...)`. Tests mock the
client, so CI never calls AWS.

## Rebuild Example Documents

The repository includes Markdown, PDF, and DOCX synthetic examples. Rebuild
them with:

```bash
make examples
```

The generated examples remain synthetic and public-safe.
