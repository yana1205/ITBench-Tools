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

from agent_bench_automation.app.config import AppConfig
from agent_bench_automation.app.models.base import BenchmarkPhaseEnum
from agent_bench_automation.app.runner import BenchmarkRunner
from agent_bench_automation.app.storage.config import StorageConfig
from agent_bench_automation.app.utils import create_status
from agent_bench_automation.common.rest_client import RestClient

logger = logging.getLogger(__name__)


class MiniBenchRunner(BenchmarkRunner):
    def __init__(
        self,
        app_config: AppConfig,
        runner_id: str,
        minibench_client: RestClient,
        interval=10,
    ) -> None:
        self.minibench_client = minibench_client
        super().__init__(app_config, runner_id, "", interval)

    def init_job_client(self):
        self.job_client = self.minibench_client

    def auth_job_client(self):
        pass

    def create_finished_status(self):
        return create_status(phase=BenchmarkPhaseEnum.PendingResultUpload)


def run(args):

    headers = {"Authorization": f"Bearer {args.remote_token}"}
    minibench_client = RestClient(
        args.minibench_host,
        args.minibench_port,
        headers=headers,
        ssl=args.minibench_ssl,
        verify=args.minibench_ssl_verify,
        root_path=args.minibench_root_path,
    )
    app_config = AppConfig(
        host=args.minibench_host,
        port=args.minibench_port,
        ssl_enabled=args.minibench_ssl,
        ssl_verify=args.minibench_ssl_verify,
        storage_config=StorageConfig(storage_type="filesystem"),
        enable_soft_delete=True,
    )

    runner = MiniBenchRunner(app_config, args.runner_id, minibench_client)
    asyncio.run(runner.run())
