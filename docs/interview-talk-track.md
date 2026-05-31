# Interview Talk Track

## 30-Second Version

CareShield is a small governed GenAI knowledge assistant built on synthetic
healthcare documents. It demonstrates the platform controls around RAG:
document parsing, chunking, embeddings, vector retrieval, role-based policy
filtering before model input, PII redaction, a model gateway abstraction,
Pydantic structured responses, citation/grounding evals, and trace events.

## 90-Second Version

I wanted a small project that shows production GenAI engineering rather than
just prompt engineering. The user asks a healthcare policy question with a role
such as nurse, billing analyst, vendor manager, or external vendor. The system
can use built-in policy documents, or it can ingest a report-like file. For
uploaded files, it parses the document, chunks it, creates deterministic local
embeddings, indexes those chunks in an in-memory vector store, builds user
context, filters by sensitivity and allowed role before retrieval, redacts
synthetic sensitive identifiers, calls a deterministic model gateway, validates
the response with Pydantic, and returns an eval report with citations,
grounding, PII redaction, policy safety, and trace events.

The key design point is that unauthorized data never enters the prompt. That is
the difference between a demo chatbot and a governed GenAI platform pattern.
The model gateway is mocked so tests are deterministic, but the same interface
could later wrap OpenAI, AWS Bedrock, Hugging Face, or a local model.

## What To Emphasize

- The document lifecycle is visible: parse -> chunk -> embed -> index -> retrieve.
- Policy happens before retrieval, not after.
- PII/PHI-style redaction happens before evidence is sent to the model gateway.
- The gateway isolates application code from provider-specific APIs.
- Pydantic turns model output into a typed contract.
- The vector store is local for CI, but the boundary maps to pgvector or
  OpenSearch Serverless.
- Evals and traces explain whether the answer is cited, grounded, redacted, and
  policy-safe.
- The project is intentionally synthetic and public-safe.

## AWS Mapping

```text
API Gateway
-> Lambda or ECS
-> parser workers for PDF / DOCX / text
-> embedding provider
-> policy/retrieval service
-> OpenSearch Serverless or Aurora pgvector
-> Bedrock or approved model gateway
-> Pydantic validation
-> CloudWatch/OpenTelemetry trace
```

## Likely Questions

**Why mock the model?**

Because the project is proving deterministic platform controls. Real provider
calls can be added behind the gateway, but unit tests should not require API
keys or live model behavior.

**Why healthcare?**

Healthcare makes the PII/PHI and access-control story obvious, while still
using only synthetic public-safe data.

**What would you improve next?**

Replace the local vector adapter with OpenSearch Serverless or Aurora pgvector,
connect the gateway to Bedrock/OpenAI through configuration, add OpenTelemetry
spans, add Terraform, and expand the CI eval dataset with golden questions.
