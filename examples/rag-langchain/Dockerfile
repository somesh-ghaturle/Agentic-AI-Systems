# 3.12, matching the interpreter `example-deps.yml` installs these pins on. This said 3.11
# until the pinned numpy dropped 3.11, at which point the image stopped building and nothing
# noticed, because CI installs the pins but never built the image.
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# Non-root. build_index.py writes index.faiss next to itself, and the embedding model is
# cached under the home directory, so the user needs both a home and ownership of /app.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
CMD ["/bin/sh", "-c", "python build_index.py && python query_and_answer.py 'reproducibility in enterprise ai'"]
