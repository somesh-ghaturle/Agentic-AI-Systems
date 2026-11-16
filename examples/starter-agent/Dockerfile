FROM python:3.11-slim
WORKDIR /app
COPY agent.py .
# Non-root: the script only reads its arguments and prints.
USER nobody
ENTRYPOINT ["python", "agent.py"]
