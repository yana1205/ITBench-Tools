FROM python:3.11.10-slim

RUN apt update -y && apt install -y curl gnupg2
RUN mkdir /etc/agent-benchmark
COPY agent_bench_automation /etc/agent-benchmark/agent_bench_automation
COPY pyproject.toml /etc/agent-benchmark/pyproject.toml
RUN pip install --upgrade setuptools==70.0.0
RUN pip install -e /etc/agent-benchmark --no-cache-dir
COPY docs /etc/agent-benchmark/docs
COPY data /etc/agent-benchmark/data
RUN ln -sf /bin/bash /bin/sh

WORKDIR /etc/agent-benchmark
