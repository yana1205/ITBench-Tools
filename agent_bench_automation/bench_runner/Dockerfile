FROM python:3.11.10

RUN mkdir /etc/agent-benchmark
COPY agent_bench_automation /etc/agent-benchmark/agent_bench_automation
COPY pyproject.toml /etc/agent-benchmark/pyproject.toml
RUN pip install -e /etc/agent-benchmark
COPY docs /etc/agent-benchmark/docs
COPY data /etc/agent-benchmark/data
RUN ln -sf /bin/bash /bin/sh

WORKDIR /etc/agent-benchmark
