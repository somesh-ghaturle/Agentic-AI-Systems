FROM python:3.12-slim

RUN useradd --create-home --uid 10001 edge
WORKDIR /app
COPY agent.py README.md ./
RUN mkdir /data && chown edge:edge /data
USER edge

ENTRYPOINT ["python", "agent.py"]
