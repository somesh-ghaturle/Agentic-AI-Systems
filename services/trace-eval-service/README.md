# Trace Eval Service

This service exposes the repository's trace-level evaluation logic through a small FastAPI
endpoint. It is designed for local development and CI smoke checks rather than production
traffic.

## Endpoints

- `GET /healthz` — returns service status
- `POST /score` — scores a trace and answer payload

## Published image

Version tags publish the image to GitHub Container Registry through
[publish-image.yml](../../.github/workflows/publish-image.yml). The workflow starts the
container and checks `/healthz` before it pushes anything.

```bash
docker run --rm -p 8000:8000 ghcr.io/somesh-ghaturle/trace-eval-service:latest
```

To build it yourself from the repository root, run this:

```bash
docker build -f services/trace-eval-service/Dockerfile -t trace-eval-service .
```

## Example

```bash
python3 -m uvicorn trace_eval_service.app:app --host 127.0.0.1 --port 8000
```

Then post JSON such as:

```json
{
  "trace": [
    {"trace_id": "t1", "seq": 1, "event": "request.received"},
    {"trace_id": "t1", "seq": 2, "event": "request.classified", "intent": "research"},
    {"trace_id": "t1", "seq": 3, "event": "request.completed", "intent": "research"}
  ],
  "expected_answer": "incident summary",
  "expected_intent": "research",
  "expected_terminal": "completed",
  "grading_criteria": {"must_mention": ["incident", "summary"]}
}
```
