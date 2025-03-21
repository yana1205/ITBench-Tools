FROM python:3.11.10-slim

RUN apt update -y && apt install -y curl gnupg2 unzip
RUN mkdir /etc/agent-benchmark
COPY itbench_tools /etc/agent-benchmark/itbench_tools
COPY pyproject.toml /etc/agent-benchmark/pyproject.toml
RUN pip install --upgrade setuptools==70.0.0
RUN pip install -e /etc/agent-benchmark --no-cache-dir
RUN ln -sf /bin/bash /bin/sh

# TODO: consider how to handle deps dynamically
#######################################
# Install caa-bundle dependencies 
#######################################

# install `ansible-playbook`
RUN pip install ansible-core jmespath kubernetes==31.0.0 --no-cache-dir
RUN ansible-galaxy collection install kubernetes.core
# install `helm`
RUN curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | tee /usr/share/keyrings/helm.gpg > /dev/null && \
    apt install apt-transport-https --yes && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | tee /etc/apt/sources.list.d/helm-stable-debian.list && \
    apt update && \
    apt install -y helm
# install `jq`
RUN apt install -y jq
# install `make`
RUN apt install -y make
# install `kubectl`
RUN curl -LO https://dl.k8s.io/release/v1.31.0/bin/linux/$(dpkg --print-architecture)/kubectl && \
    chmod +x ./kubectl && \
    mv ./kubectl /usr/local/bin/kubectl
# install `aws` (need this for using kubectl against AWS cluster)
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install
# install `opa`
RUN curl -L -o opa https://github.com/open-policy-agent/opa/releases/download/v1.0.0/opa_linux_$(dpkg --print-architecture)_static && \
    chmod +x ./opa && \
    mv ./opa /usr/local/bin/opa

WORKDIR /etc/agent-benchmark
