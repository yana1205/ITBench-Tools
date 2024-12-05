import logging
import time
from pathlib import Path
from typing import List

from agent_bench_automation.agent_operator import AgentOperator
from agent_bench_automation.app.models.agent import Agent, AgentManifest, AgentBenchmarkEntry
from agent_bench_automation.app.models.base import AgentPhaseEnum, BundlePhaseEnum, Status
from agent_bench_automation.app.models.bundle import Bundle
from agent_bench_automation.app.models.registry import BenchmarkInfo
from agent_bench_automation.common.rest_client import RestClient
from agent_bench_automation.models.agent import AgentInfo

logger = logging.getLogger(__name__)


def run(args):

    with open(args.input) as f:
        agent_manifest = AgentManifest.model_validate_json(f.read())

    rest_client = RestClient(args.host, args.port, headers={"Authorization": f"Bearer {agent_manifest.token}"})

    timeout = 3600
    interval = 5
    elapsed_time = 0
    while elapsed_time < timeout:
        entries: List[AgentBenchmarkEntry] = []
        try:
            manifest_endpoint = f"{agent_manifest.manifest_endpoint}"
            response = rest_client.get(manifest_endpoint)
            data = response.json()
            agent_manifest = AgentManifest.model_validate(data)
            entries = agent_manifest.benchmark_entries
        except Exception as e:
            logger.error(f"Failed to get manifests: {e}")

        logger.info(f"The number of benchmark entries: {len(entries)}")
        benchmatk_statuses = [f"{x.benchmark_id}: {x.status.phase}" for x in entries]
        logger.info(f"The benchmark statuses: {benchmatk_statuses}")

        entries = [x for x in entries if x.status.phase == AgentPhaseEnum.NotStarted]
        if len(entries) > 0:
            for benchmark_entry in entries:
                benchmark_id = benchmark_entry.benchmark_id
                logger.info(f"Take the benchmark '{benchmark_entry.benchmark_id}'")
                rest_client.put(
                    f"{agent_manifest.manifest_endpoint}/benchmark-entries/{benchmark_id}", Status(phase=AgentPhaseEnum.Executing).model_dump_json()
                )
                is_completed = run_benchmark(rest_client, args.agent_directory, benchmark_id, benchmark_entry.agent_access_info.id)
                if is_completed:
                    phase = AgentPhaseEnum.Finished
                else:
                    phase = AgentPhaseEnum.TimeedOut
                rest_client.put(f"{agent_manifest.manifest_endpoint}/benchmark-entries/{benchmark_id}", Status(phase=phase).model_dump_json())
        else:
            logger.info(f"No benchmark entries with status 'NotStarted' found. Wait for {interval} seconds before the next check...")
        time.sleep(interval)
        elapsed_time += interval


def run_benchmark(rest_client: RestClient, agent_directory, benchmark_id, agent_id):

    timeout = 300
    interval = 10
    elapsed_time = 0
    while elapsed_time < timeout:

        response = rest_client.get(f"/benchmarks/{benchmark_id}/bundles/")
        data = response.json()
        bundles = [Bundle.model_validate(x) for x in data]
        num_of_targets = len(bundles)

        ready_targets = [x for x in bundles if x.status.phase == BundlePhaseEnum.Ready]
        finished_targets = [x for x in bundles if x.status.phase in [BundlePhaseEnum.Terminated, BundlePhaseEnum.Error]]

        bundle_statuses = [f"{x.spec.name}:{x.status.phase}" for x in bundles]
        logger.info(f"The bundles status: {bundle_statuses}")

        if len(finished_targets) == num_of_targets:
            logger.info("All targets are finished.")
            return True

        if len(ready_targets) > 0:
            target = ready_targets[0]
            logger.info(f"Take '{target.spec.name}'")
            run_agent(rest_client, target, benchmark_id, agent_id, agent_directory)
            logger.info(f"Finished '{target.spec.name}'")
        else:
            logger.info(f"Waiting for a target to be Ready phase...")

            time.sleep(interval)
            elapsed_time += interval

    logger.error("Timeout reached while waiting for targets to leave Ready phase.")
    return False


def run_agent(rest_client: RestClient, target_bundle: Bundle, benchmark_id: str, agent_id: str, agent_directory: str):
    response = rest_client.get(f"/benchmarks/{benchmark_id}/agents/{agent_id}")
    agent = Agent.model_validate(response.json())
    agent_info = AgentInfo(id=agent.metadata.id, name=agent.spec.name, directory=agent_directory)
    ao = AgentOperator(agent_info=agent_info)
    rest_client.assign(benchmark_id, agent_id, target_bundle.metadata.id)
    rest_client.push_agent_status(benchmark_id, agent_id, AgentPhaseEnum.Executing)
    try:
        shared_workspace = Path("/tmp") / "shared_workspace" / agent.metadata.id / target_bundle.spec.name
        shared_workspace.mkdir(parents=True, exist_ok=True)
        output_dir_per_bundle = Path("/tmp") / "output" / agent.metadata.id / target_bundle.spec.name
        output_dir_per_bundle.mkdir(parents=True, exist_ok=True)
        stdout = ao.invoke_agent(target_bundle.spec.name, shared_workspace, target_bundle.spec.data, output_dir_per_bundle)
        rest_client.push_agent_status(benchmark_id, agent_id, AgentPhaseEnum.Finished, message=stdout)
    except Exception as e:
        logger.error(e)
        rest_client.push_agent_status(benchmark_id, agent_id, AgentPhaseEnum.Error, message=f"{e}")

    def wait_bundle_finished():
        logger.info(f"Wait for bundle to finish...")
        response = rest_client.get(f"/benchmarks/{benchmark_id}/bundles/{target_bundle.metadata.id}")
        data = response.json()
        bundle = Bundle.model_validate(data)
        if bundle.status.phase in [BundlePhaseEnum.Terminated, BundlePhaseEnum.Error]:
            return True
        return False

    wait(wait_bundle_finished, timeout=30, interval=5)
    rest_client.push_agent_status(benchmark_id, agent_id, AgentPhaseEnum.Ready)


def wait(callback, timeout=300, interval=10):
    timeout = 300
    interval = 10
    elapsed_time = 0
    while elapsed_time < timeout:
        if callback():
            return
        time.sleep(interval)
        elapsed_time += interval
