FROM cgr.dev/chainguard/python:latest-dev AS builder

WORKDIR /app

RUN python -m venv /venv
ENV PATH="/venv/bin:${PATH}"

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

ENV PATH="/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /venv /venv

EXPOSE 8088

CMD ["python", "-m", "uvicorn", "careshield.interfaces.api:app", "--host", "0.0.0.0", "--port", "8088"]
