# Copyright contributors to the ITBench project. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging
from typing import List, Optional, TypeVar

from requests import HTTPError

from agent_bench_automation.app.models.agent import Agent
from agent_bench_automation.app.models.base import BenchmarkPhaseEnum
from agent_bench_automation.app.models.benchmark import (
    Benchmark,
    BenchmarkJob,
    BenchmarkJobTake,
)
from agent_bench_automation.app.models.bundle import Bundle
from agent_bench_automation.app.models.registry import BenchmarkInfo
from agent_bench_automation.app.models.result import Result
from agent_bench_automation.app.utils import create_status
from agent_bench_automation.common.rest_client import RestClient

logger = logging.getLogger(__name__)


class BenchmarkTaker:

    def __init__(self, runner_id, remote_rest_client: RestClient, minibench_rest_client: RestClient):
        self.runner_id = runner_id
        self.max_concurrent_tasks = 1
        self.running_tasks = 0
        self.remote_rest_client = remote_rest_client
        self.minibench_rest_client = minibench_rest_client
        self.status_sync_interval = 10

    async def run(self):
        timeout = 3600
        interval = 5
        elapsed_time = 0
        while elapsed_time < timeout:
            try:
                benchmarks: List[Benchmark] = []

                try:
                    response = self.remote_rest_client.get("/benchmarks/queue/list_benchmark_jobs")
                    data = response.json()
                    jobs = [BenchmarkJob.model_validate(x) for x in data]
                    benchmarks = [x.benchmark for x in jobs]
                except Exception as e:
                    logger.error(f"Failed to get benchmarks from remote bench server: {e}")
                    raise e

                mini_benchmarks: List[Benchmark] = []
                try:
                    response = self.minibench_rest_client.get("/benchmarks/queue/list_benchmark_jobs")
                    data = response.json()
                    mini_benchmark_jobs = [BenchmarkJob.model_validate(x) for x in data]
                    mini_benchmarks = [x.benchmark for x in mini_benchmark_jobs]
                except Exception as e:
                    logger.error(f"Failed to get benchmarks from minibench: {e}")
                    raise e

                logger.info(f"The number of benchmarks in remote bench server: {len(benchmarks)}")
                logger.info(f"The number of benchmarks in minibench server: {len(mini_benchmarks)}")

                benchmark_map = {x.metadata.id: x for x in benchmarks}
                mini_benchmark_map = {x.metadata.id: x for x in mini_benchmarks}

                new_entries = list(set(benchmark_map.keys()) - set(mini_benchmark_map.keys()))
                existing_entries = list(set(benchmark_map.keys()) & set(mini_benchmark_map.keys()))
                obsolete_entries = list(set(mini_benchmark_map.keys()) - set(benchmark_map.keys()))

                if new_entries:
                    logger.info(f"New benchmark entries are detected: {new_entries}.")
                    added_benchmark_ids: List[str] = []
                    for benchmark_id in new_entries:
                        benchmark = benchmark_map[benchmark_id]
                        if benchmark.status.phase != BenchmarkPhaseEnum.Queued:
                            continue
                        if benchmark.spec.runner_id and benchmark.spec.runner_id != "" and benchmark.spec.runner_id != self.runner_id:
                            logger.info(f"The benchmark '{benchmark_id}' is already taken by runner '{benchmark.spec.runner_id}'")
                            continue
                        added_benchmark_ids.append(benchmark_id)

                    logger.info(f"Added benchmarks (queued benchmarks): {added_benchmark_ids}")
                    for benchmark_id in added_benchmark_ids:
                        benchmark = benchmark_map[benchmark_id]
                        if benchmark.spec.runner_id != self.runner_id:
                            success, message = take_job(benchmark_id, self.runner_id, self.remote_rest_client)
                            if not success:
                                logger.info(f"Failed to take benchmark '{benchmark_id}'. Reason: {message}")
                                continue
                        response = self.remote_rest_client.get(f"/registry/get-benchmark?benchmark_id={benchmark_id}", params={"status": True})
                        data = response.json()
                        benchmark_info = BenchmarkInfo.model_validate(data)
                        response = self.minibench_rest_client.post("/mini-bench", benchmark_info.model_dump_json())
                        response.raise_for_status()

                if existing_entries:
                    logger.info(f"Existing benchmark entries are detected: {existing_entries}.")
                    synced_benchmark_ids: List[str] = []
                    for benchmark_id in existing_entries:
                        benchmark = benchmark_map[benchmark_id]
                        if benchmark.status.phase in [BenchmarkPhaseEnum.Finished, BenchmarkPhaseEnum.Error]:
                            continue
                        if benchmark.spec.runner_id and benchmark.spec.runner_id != "" and benchmark.spec.runner_id == self.runner_id:
                            synced_benchmark_ids.append(benchmark_id)
                        else:
                            logger.info(f"Skipping task: runner ID '{benchmark.spec.runner_id}' does not match this runner's ID '{self.runner_id}'.")
                    logger.info(f"Upsync statuses of benchmarks: {synced_benchmark_ids}")
                    for benchmark_id in synced_benchmark_ids:
                        mini_benchmark = mini_benchmark_map[benchmark_id]
                        benchmark = benchmark_map[benchmark_id]
                        self.sync_status(mini_benchmark, benchmark)
                        if benchmark.status.phase == BenchmarkPhaseEnum.PendingResultUpload:
                            self.sync_results(mini_benchmark)

                if obsolete_entries:
                    logger.warning(f"Obsolete benchmarks are detected: {obsolete_entries}")
            except HTTPError as e:
                logger.error(f"HTTP Error happens in the loop: {e}")
                logger.error(f"{e.response.json()}")
            except Exception as e:
                logger.error(f"Exception happens in the loop: {e}")
            finally:
                logger.info(f"Next sync will occur in {interval} seconds.")
                await asyncio.sleep(interval)
                elapsed_time += interval

    def sync_status(self, benchmark: Benchmark, remote_benchmark: Benchmark):
        benchmark_id = benchmark.metadata.id
        logger.info(f"Sync benchmark {benchmark_id}")

        response = self.minibench_rest_client.get(f"/benchmarks/{benchmark_id}/bundles/")
        bundles: List[Bundle] = [Bundle.model_validate(x) for x in response.json()]
        if len(bundles) > 0:
            response = self.remote_rest_client.get(f"/benchmarks/{benchmark_id}/bundles/")
            remote_bundles: List[Bundle] = [Bundle.model_validate(x) for x in response.json()]
        else:
            remote_bundles: List[Bundle] = []

        response = self.minibench_rest_client.get(f"/benchmarks/{benchmark_id}/agents/")
        agents: List[Agent] = [Agent.model_validate(x) for x in response.json()]
        if len(agents) > 0:
            response = self.remote_rest_client.get(f"/benchmarks/{benchmark_id}/agents/")
            remote_agents: List[Agent] = [Agent.model_validate(x) for x in response.json()]
        else:
            remote_agents: List[Bundle] = []

        T = TypeVar("T", Agent, Bundle)

        def find_resource(resource: T, remote_resources: List[T]) -> Optional[T]:
            res = [x for x in remote_resources if x.metadata.id == resource.metadata.id]
            return res[0] if len(res) > 0 else None

        def get_updated_resources(resources: List[T], remote_resources: List[T]) -> List[T]:
            update_resources: List[T] = []
            for resource in resources:
                remote_resource = find_resource(resource, remote_resources)
                if remote_resource:
                    if remote_resource.status.phase != resource.status.phase or remote_resource.status.message != resource.status.message:
                        update_resources.append(resource)
            return update_resources

        update_bundles = get_updated_resources(bundles, remote_bundles)
        if len(update_bundles) == 0:
            logger.info("All bundles' statuses are already in sync.")
        else:
            logger.info(f"{len(update_bundles)} bundle(s) are upsynced: {[x.metadata.id for x in update_bundles]}")
            for update_bundle in update_bundles:
                id = update_bundle.metadata.id
                status = update_bundle.status
                self.remote_rest_client.put(f"/benchmarks/{benchmark_id}/bundles/{id}/status", status.model_dump_json())

        update_agents = get_updated_resources(agents, remote_agents)
        if len(update_agents) == 0:
            logger.info("All agents' statuses are already in sync.")
        else:
            logger.info(f"{len(update_agents)} agent(s) are upsynced: {[x.metadata.id for x in update_agents]}")
            for update_agent in update_agents:
                id = update_agent.metadata.id
                status = update_agent.status
                self.remote_rest_client.put(f"/benchmarks/{benchmark_id}/agents/{id}/status", status.model_dump_json())

        if remote_benchmark.status.phase != benchmark.status.phase or remote_benchmark.status.message != benchmark.status.message:
            logger.info(f"Benchmark '{benchmark.metadata.id}' is upsynced.")
            self.remote_rest_client.put(f"/benchmarks/{benchmark_id}/status", benchmark.status.model_dump_json())
        else:
            logger.info(f"Benchmark '{benchmark.metadata.id}' is already in sync.")

    def sync_results(self, benchmark: Benchmark):
        benchmark_id = benchmark.metadata.id
        response = self.minibench_rest_client.get(f"/benchmarks/{benchmark_id}/results/")
        data = response.json()
        results = [Result.model_validate(x) for x in data]
        body = [x.spec.model_dump_json() for x in results]
        body = ",".join(body)  # TODO: consider to use request.post(json=body)
        body = f"[{body}]"
        response = self.remote_rest_client.post(f"/benchmarks/{benchmark_id}/results/bulk", body)
        if response.status_code != 201:
            message = f"Failed to push results. benchmark_id: '{benchmark.metadata.id}', details: {response.text}"
            logger.error(message)
            status = create_status(phase=BenchmarkPhaseEnum.Error, message=message)
        else:
            status = create_status(phase=BenchmarkPhaseEnum.Finished)
        self.remote_rest_client.put(f"/benchmarks/{benchmark_id}/status", status.model_dump_json())
        self.minibench_rest_client.put(f"/benchmarks/{benchmark_id}/status", status.model_dump_json())


def take_job(benchmark_id: str, runner_id: str, rest_client: RestClient):
    body = BenchmarkJobTake(runner_id=runner_id)
    response = rest_client.put(f"/benchmarks/{benchmark_id}/take_benchmark_job", body=body.model_dump_json())
    data = response.json()
    success = data["success"] if "success" in data else False
    message = data["message"] if "message" in data else ""
    return success, message


def run(args):

    headers = {"Authorization": f"Bearer {args.remote_token}"}
    remote_rest_client = RestClient(
        args.remote_host,
        args.remote_port,
        headers=headers,
        ssl=args.remote_ssl,
        verify=args.remote_ssl_verify,
        root_path=args.remote_root_path,
    )
    minibench_rest_client = RestClient(
        args.minibench_host,
        args.minibench_port,
        headers=headers,
        ssl=args.minibench_ssl,
        verify=args.minibench_ssl_verify,
        root_path=args.minibench_root_path,
    )
    taker = BenchmarkTaker(args.runner_id, remote_rest_client, minibench_rest_client)
    asyncio.run(taker.run())
