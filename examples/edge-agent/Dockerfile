FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

RUN useradd --create-home --uid 10001 edge
WORKDIR /app
COPY agent.py README.md ./
RUN mkdir /data && chown edge:edge /data
USER edge

ENTRYPOINT ["python", "agent.py"]
