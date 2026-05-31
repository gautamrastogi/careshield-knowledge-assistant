# Examples

CareShield ships with synthetic documents that exercise the ingestion pipeline:

- `examples/synthetic-care-report.md`
- `examples/synthetic-care-report.pdf`
- `examples/synthetic-care-report.docx`

All three describe the same fictional care-sharing scenario. They exist so the
parsers, chunking logic, Chroma indexing, retrieval filters, redaction, and
evals can be tested against realistic file formats.

## CLI Examples

Markdown:

```bash
uv run careshield analyze-doc \
  --file examples/synthetic-care-report.md \
  --role nurse \
  --question "What must be redacted before vendor sharing?"
```

PDF:

```bash
uv run careshield analyze-doc \
  --file examples/synthetic-care-report.pdf \
  --role compliance_officer \
  --question "Which controls are required before external sharing?"
```

Word:

```bash
uv run careshield analyze-doc \
  --file examples/synthetic-care-report.docx \
  --role vendor_manager \
  --sensitivity internal \
  --question "What information can be shared with an external vendor?"
```

## API Upload Example

```bash
curl -s http://127.0.0.1:8088/documents/analyze \
  -F "file=@examples/synthetic-care-report.pdf" \
  -F "role=compliance_officer" \
  -F "sensitivity=clinical" \
  -F "question=Which controls are required before external sharing?" \
  | python -m json.tool
```

## What To Look For

The response should include:

- ingestion metadata with parser name, chunk count, embedding model, and vector count
- citations from authorized chunks only
- redaction labels such as `patient_name`, `phone`, `email`, or `medical_record_number`
- eval status for citations, groundedness, PII redaction, and policy safety
- trace steps showing parse, chunk, vector index, retrieval, gateway, evals, and validation
