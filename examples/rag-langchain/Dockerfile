FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt
CMD ["/bin/sh", "-c", "python build_index.py && python query_and_answer.py 'reproducibility in enterprise ai'"]
