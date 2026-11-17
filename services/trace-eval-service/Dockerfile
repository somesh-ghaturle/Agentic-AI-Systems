FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

WORKDIR /app

COPY services/trace-eval-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY trace_eval_service ./trace_eval_service
COPY examples/trace-eval/traceeval ./examples/trace-eval/traceeval

# Non-root. This is the one image the repository publishes, and the service writes nothing
# to disk, so there is no reason for the process to hold root inside the container.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "trace_eval_service.app:app", "--host", "0.0.0.0", "--port", "8000"]
