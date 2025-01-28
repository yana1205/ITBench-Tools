#!/bin/bash

remote_host=$1
remote_port=$2
agent_api_name=$3
agent_api_port=$4
agent_id=$5
agent_token=$6

endpoint="https://$remote_host"
if [[ $remote_port -gt 0 ]]; then
        endpoint="https://$remote_host:$remote_port"
fi

curl -k -s -X GET -H "Authorization: Bearer $agent_token" "$endpoint/registry/agent-manifest/$agent_id" > /tmp/agent-manifest.json
echo "Agent manifest has been obtained."

python -u agent_bench_automation/agent_harness/main.py \
        --host $agent_api_name \
        --port $agent_api_port \
        --agent_directory /app/lumyn \
        -c ./docs/scenario-support/agent-harness-sre.yaml \
        -i /tmp/agent-manifest.json \
        --ssl \
        --benchmark_timeout 3000