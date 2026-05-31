.PHONY: install test demo demo-doc api docker-build

install:
	uv sync --dev

test:
	uv run pytest -q

demo:
	uv run careshield ask --role nurse --question "Can I send a patient discharge summary to an external vendor?"

demo-doc:
	uv run careshield analyze-doc --file examples/synthetic-care-report.md --role nurse --question "What must be redacted before vendor sharing?"

api:
	uv run uvicorn careshield.api:app --reload --host 127.0.0.1 --port 8088

docker-build:
	docker build -t careshield-knowledge-assistant .
