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
from pathlib import Path
from typing import List, Optional

import yaml

import agent_bench_automation.benchmark
from agent_bench_automation.app.config import SERVICE_API_KEY, AppConfig
from agent_bench_automation.app.models.agent import Agent as AgentInApp
from agent_bench_automation.app.models.agent import AgentManifest
from agent_bench_automation.app.models.base import BenchmarkPhaseEnum
from agent_bench_automation.app.models.benchmark import (
    Benchmark,
    BenchmarkJob,
    BenchmarkJobTake,
)
from agent_bench_automation.app.models.bundle import Bundle as BundleInApp
from agent_bench_automation.app.utils import create_status, get_tempdir
from agent_bench_automation.common.rest_client import RestClient
from agent_bench_automation.models.agent import AgentInfo
from agent_bench_automation.models.benchmark import BenchConfig, BenchRunConfig
from agent_bench_automation.models.bundle import Bundle

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    def __init__(
        self,
        app_config: AppConfig,
        runner_id: str,
        service_type: str,
    ) -> None:
        self.app_config = app_config
        self.runner_id = runner_id
        self.host = app_config.host
        self.port = app_config.port
        self.ssl = app_config.ssl_enabled
        self.ssl_verify = app_config.ssl_verify
        self.max_concurrent_tasks = 1
        self.running_tasks = 0
        self.interval = 10
        self.service_type = service_type
        self.service_client: RestClient

    async def run(self):

        service_accounts = [x for x in self.app_config.service_accounts if x.type == self.service_type]
        if len(service_accounts) == 0:
            raise Exception("Please specify correct service type")
        service_account = service_accounts[0]
        self.service_client = RestClient(self.host, self.port, ssl=self.ssl, verify=self.ssl_verify)
        self.service_client.login(service_account.id, SERVICE_API_KEY)

        while True:
            if self.running_tasks < self.max_concurrent_tasks:
                logger.info("Fetch benchmark jobs...")
                self.service_client.login(service_account.id, SERVICE_API_KEY)
                response = self.service_client.get("/benchmarks/queue/list_benchmark_jobs")
                data = response.json()
                jobs = [BenchmarkJob.model_validate(x) for x in data]
                if len(jobs) == 0:
                    logger.info(f"There are no benchmark jobs. Wait for '{self.interval}s' the next poll..")
                for job in jobs:
                    benchmark_id = job.benchmark.metadata.id
                    body = BenchmarkJobTake(runner_id=self.runner_id)
                    response = self.service_client.put(f"/benchmarks/{benchmark_id}/take_benchmark_job", body=body.model_dump_json())
                    data = response.json()
                    if data["success"] == True:
                        logger.info(f"Benchmark job '{benchmark_id}' is successfully taken. Start benchmark...")
                        self.running_tasks += 1
                        asyncio.create_task(self.run_benchmark(job.benchmark, job.agent_manifest))
                    else:
                        logger.info(f"Benchmark job '{benchmark_id}' is not successfully assigned.")
            else:
                logger.info("The number of current task is over max concurrent jobs. Wait for the runner to be available.")
            await asyncio.sleep(self.interval)

    async def run_benchmark(self, benchmark: Benchmark, agent_manifest: AgentManifest):
        benchmark_id = benchmark.metadata.id
        token = agent_manifest.token
        headers = {"Authorization": f"Bearer {token}"}
        client = RestClient(self.host, self.port, headers=headers, ssl=self.ssl, verify=self.ssl_verify)
        base_endpoint = f"/benchmarks/{benchmark_id}"
        try:
            response = client.get(f"{base_endpoint}/bundles")
            _bundles = [BundleInApp.model_validate(x) for x in response.json()]

            response = client.get(f"{base_endpoint}/agents")
            _agents = [AgentInApp.model_validate(x) for x in response.json()]

            bench_run_config = build_benchmark_run_config(
                benchmark,
                _agents,
                _bundles,
                self.app_config.enable_soft_delete,
                self.interval,
            )

            _logger = setup_request_logger(benchmark_id)
            logfilepath = get_specific_log_file_path(_logger, benchmark_id)
            benchmark_runner = agent_bench_automation.benchmark.Benchmark(_logger=_logger)

            benchmark.status = create_status(phase=BenchmarkPhaseEnum.Running)
            benchmark.spec.log_file_path = logfilepath
            client.put(f"{base_endpoint}/update_benchmark_job", benchmark.model_dump_json())
            benchmark_runner.run_benchmark(bench_run_config, client)

            benchmark.status = create_status(phase=BenchmarkPhaseEnum.Finished)
            client.put(f"{base_endpoint}/update_benchmark_job", benchmark.model_dump_json())
            logger.info("Benchmarking is finished")
            self.running_tasks -= 1
        except Exception as e:
            message = f"Error while running benchmark '{benchmark.metadata.id}': {e}"
            logger.error(message)
            self.running_tasks -= 1
            benchmark.status = create_status(phase=BenchmarkPhaseEnum.Error, message=message)
            try:
                response = self.service_client.put(f"/benchmarks/{benchmark_id}/release_benchmark_job")
                if not response.json()["success"]:
                    raise Exception(f"{response.text}")
            except Exception as e:
                message = f"Failed to release job of benchmark id '{benchmark.metadata.id}': {e}"
                logger.error(message)
                benchmark.status.message = benchmark.status.message + "\n" + message
            try:
                client.put(f"{base_endpoint}/update_benchmark_job", benchmark.model_dump_json())
            except Exception as e:
                logger.error(f"Failed to update status of benchmark id '{benchmark.metadata.id}': {e}")


def build_benchmark_run_config(
    benchmark: Benchmark,
    agents: List[AgentInApp],
    bundles: List[BundleInApp],
    enable_safe_delete: Optional[bool] = False,
    interval: Optional[int] = None,
) -> BenchRunConfig:
    benchmark_id = benchmark.metadata.id
    agent_infos = [AgentInfo(id=x.metadata.id, name=x.spec.name, directory=x.spec.path if x.spec.path else "", mode=x.spec.mode) for x in agents]
    _bundles = [
        Bundle(
            id=x.metadata.id,
            name=x.spec.name,
            incident_type=x.spec.scenario_type,
            bundle_ready_timeout=x.spec.bundle_ready_timeout,
            agent_operation_timeout=x.spec.agent_operation_timeout,
            directory=f"{x.spec.root_dir}/{x.spec.path}" if x.spec.root_dir else x.spec.path,
            params=x.spec.params,
            input=x.spec.data["input"] if x.spec.data and "input" in x.spec.data else None,
            env=x.spec.env,
            make_target_mapping=x.spec.make_target_mapping,
            enable_evaluation_wait=x.spec.enable_evaluation_wait,
            use_input_file=False,
        )
        for x in bundles
    ]

    bench_config = BenchConfig(title=benchmark.spec.name, is_test=False, soft_delete=enable_safe_delete)
    bench_run_config = BenchRunConfig(
        benchmark_id=benchmark_id,
        push_model=True,
        config=bench_config,
        agents=agent_infos,
        bundles=_bundles,
        output_dir=get_tempdir(benchmark_id),
        interval=interval,
    )
    return bench_run_config


def setup_request_logger(benchmark_id: str, debug=False) -> logging.Logger:
    logger = logging.getLogger(benchmark_id)
    log_format = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s")
    log_file_name = f"log_{benchmark_id}.log"

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_name)
    if debug:
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger


def get_specific_log_file_path(logger_instance, benchmark_id):
    for handler in logger_instance.handlers:
        if isinstance(handler, logging.FileHandler) and benchmark_id in handler.baseFilename:
            return handler.baseFilename
    return None


def run(args):

    config_path = args.config
    with Path(config_path).open("r") as f:
        data = yaml.safe_load(f)
        app_config = AppConfig.model_validate(data)
    runner = BenchmarkRunner(app_config, args.runner_id, args.service_type)
    asyncio.run(runner.run())
