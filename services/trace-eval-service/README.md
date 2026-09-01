# Trace Eval Service

This service exposes the repository's trace-level evaluation logic through a small FastAPI
endpoint. It is designed for local development and CI smoke checks rather than production
traffic.

## Endpoints

- `GET /healthz` — returns service status
- `POST /score` — scores a trace and answer payload

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
