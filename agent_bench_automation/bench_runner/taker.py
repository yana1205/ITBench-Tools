# Copyright (c) 2024 IBM Corp. All rights reserved.
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
from typing import List, Optional

from agent_bench_automation.app.models.agent import Agent
from agent_bench_automation.app.models.base import BenchmarkPhaseEnum, BundlePhaseEnum
from agent_bench_automation.app.models.bundle import Bundle
from agent_bench_automation.app.models.registry import BenchmarkInfo
from agent_bench_automation.app.utils import create_status
from agent_bench_automation.common.rest_client import RestClient

logger = logging.getLogger(__name__)


class BenchmarkTaker:

    def __init__(self, remote_rest_client: RestClient, minibench_rest_client: RestClient):
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
            benchmark_infos: List[BenchmarkInfo] = []
            try:
                response = self.remote_rest_client.get("/registry/list-benchmark", params={"status": True})
                data = response.json()
                benchmark_infos = [BenchmarkInfo.model_validate(x) for x in data]
                benchmark_infos = [x for x in benchmark_infos if x.status.phase == BenchmarkPhaseEnum.Queued]
            except Exception as e:
                logger.error(f"Failed to get benchmarks from remote bench server: {e}")

            mini_benchmark_infos: List[BenchmarkInfo] = []
            try:
                response = self.minibench_rest_client.get("/registry/list-benchmark")
                data = response.json()
                mini_benchmark_infos = [BenchmarkInfo.model_validate(x) for x in data]
            except Exception as e:
                logger.error(f"Failed to get benchmarks from minibench: {e}")

            logger.info(f"The number of benchmarks in remote bench server: {len(benchmark_infos)}")
            logger.info(f"The number of benchmarks in minibench server: {len(mini_benchmark_infos)}")

            benchmark_info_ids = [x.id for x in benchmark_infos]
            mini_benchmark_info_ids = [x.id for x in mini_benchmark_infos]

            diff = list(set(benchmark_info_ids) - set(mini_benchmark_info_ids))

            if diff:
                logger.info(f"New benchmarks are detected: {diff}")
                for benchmark_id in diff:
                    response = self.remote_rest_client.get(f"/registry/get-benchmark?benchmark_id={benchmark_id}")
                    data = response.json()
                    benchmark_info = BenchmarkInfo.model_validate(data)

                    status = create_status(phase=BenchmarkPhaseEnum.Running)
                    self.remote_rest_client.put(f"/benchmarks/{benchmark_id}/status", status.model_dump_json())
                    response = self.minibench_rest_client.post("/mini-bench", benchmark_info.model_dump_json())
                    response.raise_for_status()
                    await self.sync_status(benchmark_info.id, benchmark_info.agent_access.id)
                    status = create_status(phase=BenchmarkPhaseEnum.Finished)
                    self.remote_rest_client.put(f"/benchmarks/{benchmark_id}/status", status.model_dump_json())
            else:
                logger.info(f"No new benchmarks come. Wait for {interval} seconds before the next check...")
            await asyncio.sleep(interval)
            elapsed_time += interval

    async def sync_status(self, benchmark_id: str, agent_id):
        while True:
            response = self.minibench_rest_client.get(f"/benchmarks/{benchmark_id}/bundles/")
            bundles: List[Bundle] = [Bundle.model_validate(x) for x in response.json()]
            response = self.remote_rest_client.get(f"/benchmarks/{benchmark_id}/bundles/")
            remote_bundles: List[Bundle] = [Bundle.model_validate(x) for x in response.json()]

            def find_bundle(bundle: Bundle) -> Optional[Bundle]:
                res = [x for x in remote_bundles if x.metadata.id == bundle.metadata.id]
                return res[0] if len(res) > 0 else None

            update_bundles: List[Bundle] = []
            for bundle in bundles:
                remote_bundle = find_bundle(bundle)
                if remote_bundle:
                    if remote_bundle.status.phase != bundle.status.phase or remote_bundle.status.message != bundle.status.message:
                        update_bundles.append(bundle)
            for update_bundle in update_bundles:
                id = update_bundle.metadata.id
                status = update_bundle.status
                self.remote_rest_client.put(f"/benchmarks/{benchmark_id}/bundles/{id}/status", status.model_dump_json())
            response = self.minibench_rest_client.get(f"/benchmarks/{benchmark_id}/agents/{agent_id}")
            agent = Agent.model_validate(response.json())
            self.remote_rest_client.put(f"/benchmarks/{benchmark_id}/agents/{agent.metadata.id}/status", agent.status.model_dump_json())

            FINISHED_STATUS = [BundlePhaseEnum.Error, BundlePhaseEnum.Terminated]
            if all([x.status.phase in FINISHED_STATUS for x in bundles]):
                logger.info("All bundle executions are finished.")
                return
            logger.info(f"Scheduled the next status update in {self.status_sync_interval} seconds.")
            await asyncio.sleep(self.status_sync_interval)


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
    taker = BenchmarkTaker(remote_rest_client, minibench_rest_client)
    asyncio.run(taker.run())
