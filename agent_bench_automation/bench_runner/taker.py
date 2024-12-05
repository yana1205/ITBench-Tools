import logging
import time
from typing import List

from agent_bench_automation.app.models.registry import BenchmarkInfo
from agent_bench_automation.common.rest_client import RestClient

logger = logging.getLogger(__name__)


def run(args):

    headers = {"Authorization": f"Bearer {args.remote_token}"}
    remote_rest_client = RestClient(args.remote_host, args.remote_port, headers=headers)
    minibench_rest_client = RestClient(args.minibench_host, args.minibench_port, headers=headers)

    timeout = 3600
    interval = 5
    elapsed_time = 0
    while elapsed_time < timeout:
        benchmark_infos: List[BenchmarkInfo] = []
        try:
            response = remote_rest_client.get("/registry/list-benchmark")
            data = response.json()
            benchmark_infos = [BenchmarkInfo.model_validate(x) for x in data]
        except Exception as e:
            logger.error(f"Failed to get benchmarks from remote bench server: {e}")

        mini_benchmark_infos: List[BenchmarkInfo] = []
        try:
            response = minibench_rest_client.get("/registry/list-benchmark")
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
                response = remote_rest_client.get(f"/registry/get-benchmark?benchmark_id={benchmark_id}")
                data = response.json()
                benchmark_info = BenchmarkInfo.model_validate(data)
                response = minibench_rest_client.post("/mini-bench", benchmark_info.model_dump_json())
        else:
            logger.info(f"No new benchmarks come. Wait for {interval} seconds before the next check...")
            time.sleep(interval)
            elapsed_time += interval
