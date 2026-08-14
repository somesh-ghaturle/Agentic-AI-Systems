FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# Non-root. The app writes its audit log and provenance files into its own directory, so
# the working tree has to be owned by the user that runs it.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
