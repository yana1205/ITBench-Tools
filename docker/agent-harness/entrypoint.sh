#!/bin/bash

###
# This entrypoint.sh file is only for development purpose at trying docker-compose.
# Now we use Kubernetes with Helm. Please refer to deployment manifests for running agent-harness.
###

remote_host=$1
remote_port=$2
agent_api_name=$3
agent_api_port=$4
agent_id=$5
agent_token=$6

echo "Installing agent..."
pip install -e /etc/mounted_agent > /dev/null
echo "The agent has been installed. Start running harness."

endpoint="$remote_host"
if [[ $remote_port -gt 0 ]]; then
        endpoint="$remote_host:$remote_port"
fi

curl -s -X GET -H "Authorization: Bearer $agent_token" "$endpoint/registry/agent-manifest/$agent_id" > /tmp/agent-manifest.json
echo "Agent manifest has been obtained."

python -u itbench_tools/agent_harness/main.py \
        --host $agent_api_name \
        --port $agent_api_port \
        --agent_directory /etc/mounted_agent \
        -i /tmp/agent-manifest.json