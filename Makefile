.PHONY: install lint format format-check typecheck test evals security examples ci demo demo-ask demo-doc api ui docker-build

UV := env -u VIRTUAL_ENV uv

install:
	@$(UV) sync --dev

test:
	@$(UV) run pytest -q

lint:
	@$(UV) run ruff check .

format:
	@$(UV) run ruff format .

format-check:
	@$(UV) run ruff format --check .

typecheck:
	@$(UV) run mypy src

evals:
	@$(UV) run pytest -q tests/test_golden_evals.py

security:
	@$(UV) run pip-audit --skip-editable

examples:
	@$(UV) run python tools/build_example_documents.py

ci: lint format-check typecheck test evals security

demo: demo-ask

demo-ask:
	@$(UV) run careshield ask --role nurse --question "Can I send a patient discharge summary to an external vendor?"

demo-doc:
	@$(UV) run careshield analyze-doc --file examples/synthetic-care-report.md --role nurse --question "What must be redacted before vendor sharing?"

api:
	@$(UV) run uvicorn careshield.interfaces.api:app --reload --host 127.0.0.1 --port 8088

ui:
	@$(UV) run streamlit run apps/streamlit_app.py

docker-build:
	@docker build -t careshield-knowledge-assistant .
