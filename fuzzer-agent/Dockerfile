FROM python:3.13-slim

WORKDIR /app

COPY fuzzer-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fuzzer-agent/src/ ./src/

# Generated test output directory (no longer strictly needed, but kept for fallback)
RUN mkdir -p /app/generated-tests

EXPOSE 8080
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]
