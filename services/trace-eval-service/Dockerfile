FROM python:3.12-slim

WORKDIR /app

COPY services/trace-eval-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY trace_eval_service ./trace_eval_service
COPY examples ./examples

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "trace_eval_service.app:app", "--host", "0.0.0.0", "--port", "8000"]
