.PHONY: install lint format format-check typecheck test evals examples ci demo demo-ask demo-doc api docker-build

install:
	uv sync --dev

test:
	uv run pytest -q

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy src

evals:
	uv run pytest -q tests/test_golden_evals.py

examples:
	uv run python tools/build_example_documents.py

ci: lint format-check typecheck test evals

demo: demo-ask

demo-ask:
	uv run careshield ask --role nurse --question "Can I send a patient discharge summary to an external vendor?"

demo-doc:
	uv run careshield analyze-doc --file examples/synthetic-care-report.md --role nurse --question "What must be redacted before vendor sharing?"

api:
	uv run uvicorn careshield.interfaces.api:app --reload --host 127.0.0.1 --port 8088

docker-build:
	docker build -t careshield-knowledge-assistant .
