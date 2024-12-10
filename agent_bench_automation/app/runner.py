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
from agent_bench_automation.app.config import (
    BENCHMARK_RESOURCE_ROOT,
    ROOT_BENCHMARK_LABEL,
    AppConfig,
)
from agent_bench_automation.app.models.agent import Agent
from agent_bench_automation.app.models.agent import Agent as AgentInApp
from agent_bench_automation.app.models.base import BenchmarkPhaseEnum
from agent_bench_automation.app.models.benchmark import Benchmark
from agent_bench_automation.app.models.bundle import Bundle as BundleInApp
from agent_bench_automation.app.storage.factory import StorageFactory, StorageInterface
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
    ) -> None:
        self.app_config = app_config
        sf = StorageFactory(storage_config=self.app_config.storage_config)
        self.bm_storage: StorageInterface[Benchmark] = sf.get_storage(Benchmark, resource_type="benchmarks")
        self.agent_storage: StorageInterface[Agent] = sf.get_storage(Agent, resource_type="agents")
        self.runner_id = runner_id
        self.host = app_config.host
        self.port = app_config.port
        self.max_concurrent_tasks = 1
        self.running_tasks = 0
        self.interval = 10

    async def run(self):

        while True:
            logger.info("Fetch benchmark entries...")
            if self.running_tasks < self.max_concurrent_tasks:
                benchmarks: List[Benchmark] = self.bm_storage.get_all(BENCHMARK_RESOURCE_ROOT)
                benchmarks = [x for x in benchmarks if not (x.metadata.labels and x.metadata.labels[ROOT_BENCHMARK_LABEL] == "true")]
                if len(benchmarks) == 0:
                    logger.info("There is no benchmark entries...")
                for benchmark in benchmarks:
                    if (
                        not benchmark.spec.runner_id
                        and benchmark.status
                        and not benchmark.status.phase in [BenchmarkPhaseEnum.Error, BenchmarkPhaseEnum.Finished]
                    ):
                        logger.info(f"Find a benchmark job '{benchmark.metadata.id}'")
                        benchmark.spec.runner_id = self.runner_id
                        agents = self.agent_storage.get_all(benchmark.metadata.id)
                        if len(agents) == 0:
                            logger.info(f"No agents are registered for benchmark '{benchmark.metadata.id}'. Skip this benchmark entry.")
                            continue
                        self.bm_storage.update(BENCHMARK_RESOURCE_ROOT, benchmark.metadata.id, benchmark)
                        if self.running_tasks < self.max_concurrent_tasks:
                            asyncio.create_task(self.run_benchmark(benchmark, agents[0]))
                        else:
                            logger.info("The number of current task is over max concurrent jobs. Wait for the runner to be available.")
                    else:
                        logger.info("There is no runner assigned benchmark entries...")
            else:
                logger.info("The number of current task is over max concurrent jobs. Wait for the runner to be available.")
            await asyncio.sleep(self.interval)

    async def run_benchmark(self, benchmark: Benchmark, agent: Agent):
        try:
            self.running_tasks += 1

            benchmark_id = benchmark.metadata.id
            token = agent.spec.agent_manifest.token
            headers = {"Authorization": f"Bearer {token}"}
            client = RestClient(self.host, self.port, headers=headers)
            base_endpoint = f"/benchmarks/{benchmark_id}"

            response = client.get(f"{base_endpoint}/bundles")
            _bundles = [BundleInApp.model_validate(x) for x in response.json()]

            response = client.get(f"{base_endpoint}/agents")
            _agents = [AgentInApp.model_validate(x) for x in response.json()]

            bench_run_config = build_benchmark_run_config(
                benchmark,
                _agents,
                _bundles,
                self.app_config.enable_soft_delete,
                self.host,
                self.port,
                token,
                self.interval,
            )

            _logger = setup_request_logger(benchmark_id)
            logfilepath = get_specific_log_file_path(_logger, benchmark_id)
            benchmark_runner = agent_bench_automation.benchmark.Benchmark(_logger=_logger)

            benchmark.status = create_status(phase=BenchmarkPhaseEnum.Running)
            benchmark.spec.log_file_path = logfilepath
            self.bm_storage.update(BENCHMARK_RESOURCE_ROOT, benchmark_id, benchmark)
            benchmark_runner.run_benchmark(bench_run_config)

            benchmark.status = create_status(phase=BenchmarkPhaseEnum.Finished)
            self.bm_storage.update(BENCHMARK_RESOURCE_ROOT, benchmark_id, benchmark)
            logger.info("Benchmarking is finished")
            self.running_tasks -= 1
        except Exception as e:
            benchmark.spec.runner_id = None
            self.running_tasks -= 1
            benchmark.status = create_status(phase=BenchmarkPhaseEnum.Error)
            self.bm_storage.update(BENCHMARK_RESOURCE_ROOT, benchmark.metadata.id, benchmark)
            error_message = f"Error while running benchmark '{benchmark.metadata.id}', agent {agent.spec.name}: {e}"
            logger.error(error_message)


def build_benchmark_run_config(
    benchmark: Benchmark,
    agents: List[AgentInApp],
    bundles: List[BundleInApp],
    enable_safe_delete: Optional[bool] = False,
    host: Optional[str] = None,
    port: Optional[int] = None,
    token: Optional[str] = None,
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
        host=host,
        port=port,
        token=token,
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
    runner = BenchmarkRunner(app_config, args.runner_id)
    asyncio.run(runner.run())
