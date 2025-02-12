FROM python:3.12-slim

WORKDIR /app

RUN apt update -y && apt install -y curl gnupg2 jq
RUN mkdir /app/agent-benchmark
COPY agent_bench_automation /app/agent-benchmark/agent_bench_automation
COPY pyproject.toml /app/agent-benchmark/pyproject.toml
RUN pip install -e /app/agent-benchmark --no-cache-dir
COPY docs /app/agent-benchmark/docs
COPY data /app/agent-benchmark/data
RUN ln -sf /bin/bash /bin/sh

WORKDIR /app/agent-benchmark
