#!/bin/bash

kops export kubecfg --admin --name=$AWX_CLUSTERNAME --state=s3://$S3_BUCKET_NAME --kubeconfig /tmp/$AWX_CLUSTERNAME.yaml
cd /etc/agent-benchmark
python agent_bench_automation/main.py runner \
    -c ./docs/scenario-support/config-sre.yaml \
    --runner_id runner1 \
    --service_type SRE