FROM python:3.11.10

RUN mkdir /etc/agent-benchmark
COPY agent_bench_automation /etc/agent-benchmark/agent_bench_automation
COPY pyproject.toml /etc/agent-benchmark/pyproject.toml
RUN pip install -e /etc/agent-benchmark
COPY docs /etc/agent-benchmark/docs
COPY data /etc/agent-benchmark/data
RUN ln -sf /bin/bash /bin/sh

# TODO: consider how to handle deps dynamically
#######################################
# Install caa-agent dependencies 
#######################################

RUN pip install -r /etc/agent-benchmark/agent_bench_automation/agent_harness/requirements.txt

# install `ansible-playbook`
RUN pip install ansible jmespath kubernetes
RUN ansible-galaxy collection install kubernetes.core
# install `jq`
RUN apt update -y && apt install -y jq
# install `kubectl`
RUN curl -LO https://dl.k8s.io/release/v1.31.0/bin/linux/$(dpkg --print-architecture)/kubectl && \
    chmod +x ./kubectl && \
    mv ./kubectl /usr/local/bin/kubectl
# install `opa`
RUN curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_$(dpkg --print-architecture) && \
    chmod +x ./opa && \
    mv ./opa /usr/local/bin/opa

WORKDIR /etc/agent-benchmark
