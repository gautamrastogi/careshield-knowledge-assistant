# CareShield Knowledge Assistant

A tiny, public-safe GenAI platform demo for synthetic healthcare policy Q&A.

The goal is not to build a flashy chatbot. The goal is to demonstrate the
production controls around a GenAI/RAG workflow:

- document ingestion for text, Markdown, PDF, and Word files
- chunking, local embeddings, and vector retrieval
- policy-aware retrieval before model input
- synthetic PII/PHI redaction
- model gateway abstraction
- Pydantic structured responses
- citation and groundedness-style evals
- trace events for debugging and audit
- CLI and FastAPI/OpenAPI entry points

All data in this repository is synthetic. It contains no real patient,
company, hospital, or production data.

## Why This Exists

Enterprise GenAI systems usually fail around the model, not inside the model:

- unauthorized documents enter the prompt
- sensitive identifiers leak into logs or responses
- provider calls are scattered across apps
- responses are loose text instead of typed contracts
- no one can prove whether an answer was grounded or cited

CareShield shows a small but complete governed flow.

```mermaid
flowchart LR
    A[PDF / DOCX / text report] --> B[Parse]
    B --> C[Chunk]
    C --> D[Embed]
    D --> E[Vector index]
    F[Question + user role] --> G[Policy filter]
    E --> G
    G --> H[Allowed vector retrieval]
    H --> I[PII redaction]
    I --> J[Model gateway mock]
    J --> K[Pydantic response validation]
    K --> L[Citation / grounding eval]
    L --> M[Trace output]
```

## Example Use Case

A nurse asks:

> Can I send a patient discharge summary to an external vendor?

CareShield:

1. Builds role context for `nurse`.
2. Filters documents before retrieval.
3. Retrieves only documents the nurse is allowed to see.
4. Redacts synthetic sensitive identifiers from evidence.
5. Calls a deterministic mock model gateway.
6. Validates the answer shape with Pydantic.
7. Checks citations, grounding, PII redaction, and policy safety.
8. Returns trace events explaining the flow.

## Quick Start

```bash
uv sync --dev
make test
make demo
make demo-doc
```

Or run directly:

```bash
uv run careshield ask \
  --role nurse \
  --question "Can I send a patient discharge summary to an external vendor?"
```

List roles:

```bash
uv run careshield roles
```

Analyze a local report-like document:

```bash
uv run careshield analyze-doc \
  --file examples/synthetic-care-report.md \
  --role nurse \
  --question "What must be redacted before vendor sharing?"
```

## API / OpenAPI Demo

Start the FastAPI app:

```bash
make api
```

Open:

```text
http://127.0.0.1:8088/docs
```

Call the API:

```bash
curl -s http://127.0.0.1:8088/ask \
  -H "content-type: application/json" \
  -d '{
    "role": "vendor_manager",
    "question": "What should be redacted before sharing data with a vendor?"
  }' | python -m json.tool
```

Analyze an uploaded document:

```bash
curl -s http://127.0.0.1:8088/documents/analyze \
  -F "file=@examples/synthetic-care-report.md" \
  -F "role=nurse" \
  -F "sensitivity=clinical" \
  -F "question=What must be redacted before vendor sharing?" \
  | python -m json.tool
```

Supported demo input formats are `.txt`, `.md`, `.pdf`, and `.docx`.

The local embedding model is `local-hash-embedding-v1`. In production this
adapter boundary is where you would use Bedrock embeddings, OpenAI embeddings,
Hugging Face embeddings, OpenSearch vector search, Aurora pgvector, or another
approved internal vector service.

## What The Response Shows

```json
{
  "answer": "Only approved, de-identified...",
  "confidence": "high",
  "citations": [
    {
      "doc_id": "patient-summary-redaction-guide",
      "title": "Patient Summary Redaction Guide"
    }
  ],
  "redactions": ["email", "phone", "medical_record_number"],
  "eval": {
    "citations_present": true,
    "grounded": true,
    "pii_redacted": true,
    "policy_safe": true,
    "score": 100
  },
  "trace": [
    {"step": "request", "status": "ok"},
    {"step": "policy_retrieval", "status": "ok"},
    {"step": "model_gateway", "status": "ok"}
  ]
}
```

## Architecture

```text
src/careshield/
  contracts/       Pydantic request and response schemas
  guardrails/      policy checks, PII redaction, and deterministic evals
  interfaces/      FastAPI/OpenAPI and CLI entry points
  pipeline/        assistant orchestration, model gateway, and trace events
  retrieval/       synthetic data, parsing, chunking, embeddings, vector search
```

## Interview Talk Track

> I built CareShield as a small governed GenAI/RAG assistant using synthetic
> healthcare policy documents. The important part is the platform control flow:
> documents can be parsed, chunked, embedded, indexed, filtered by user context,
> retrieved with authorization controls, redacted, sent through a gateway
> abstraction, validated with Pydantic, and checked by evals for citations,
> grounding, PII redaction, and policy safety. It is intentionally deterministic
> so the security and quality controls are testable offline and in CI.

## AWS Deployment Mapping

This repo runs locally by default. A production-style AWS mapping would be:

```text
API Gateway
  -> Lambda / ECS service
  -> parser workers for PDF / DOCX / text
  -> embedding provider
  -> policy and retrieval service
  -> OpenSearch Serverless or Aurora pgvector
  -> Bedrock or approved model gateway
  -> Pydantic validation
  -> CloudWatch / OpenTelemetry traces
  -> Secrets Manager and KMS
```

The demo keeps the provider mocked so tests never require API keys.

## Test Coverage

```bash
make test
```

Tests cover:

- document parsing for text and Word files
- chunking and ingestion metadata
- local embedding and vector retrieval
- role-based policy filtering
- retrieval pre-filtering
- synthetic PII redaction
- structured response validation
- citation and grounding-style evals
- FastAPI `/health`, `/ask`, and `/documents/analyze`

## Public-Safety Notes

- No real PHI/PII is stored.
- No real provider key is required.
- All examples are synthetic and safe for a public GitHub repository.
- The mock gateway exists to show platform boundaries without sending data to
  an external model provider.
