#!/bin/bash

kops export kubecfg --admin --name=$CLUSTER_NAME --state=s3://$S3NAME --kubeconfig /tmp/$CLUSTER_NAME.yaml
export KUBECONFIG=/tmp/$CLUSTER_NAME.yaml
cd /etc/agent-benchmark
python agent_bench_automation/main.py runner \
    -c ./docs/scenario-support/config-sre.yaml \
    --runner_id runner1 \
    --service_type SRE