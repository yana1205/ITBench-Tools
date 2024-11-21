import json
import sys
from pathlib import Path
from typing import Any, Dict

from caa_bench.agent_operator import AgentOperator
from caa_bench.benchmark import Benchmark, write_for_leaderboard
from caa_bench.bundle_operator import BundleOperator
from caa_bench.models.agent import AgentInfo
from caa_bench.models.benchmark import BenchConfig, BenchRunConfig
from caa_bench.models.bundle import Bundle, BundleRequest, BundleResult, BundleStatus
from tests import bundle_statues

OUTPUT_DIR = Path("tmp_test")


def get_status() -> BundleStatus:
    pass


def get_evaluation():
    pass


def gen_mock_with_status_update(monkeypatch, bundle_statuses):
    results = iter(bundle_statuses)
    mock_get_bundle_status = lambda: next(results)
    monkeypatch.setattr(sys.modules[__name__], "get_status", mock_get_bundle_status)


def gen_mock_invoke_bundle(monkeypatch):

    def mock_invoke_bundle(self, target, extra_args=[], retry=0, max_retry=1, interval=1):
        if target == "get_status":
            status_json = get_status().model_dump_json()
            data = {"status": json.loads(status_json)}
            return json.dumps(data)
        elif target == "get":
            return json.dumps({})
        elif target == "evaluate":
            gen_mock_with_status_update(monkeypatch, [bundle_statues.FAULT_INJECTED])
            return json.dumps(get_evaluation())
        elif target == "deploy_bundle":
            gen_mock_with_status_update(monkeypatch, [bundle_statues.DEPLOYING, bundle_statues.DEPLOYED])
        elif target == "inject_fault":
            monkeypatch.setattr(sys.modules[__name__], "get_evaluation", lambda: {"pass": False, "report": []})
            gen_mock_with_status_update(monkeypatch, [bundle_statues.FAULT_INJECTING, bundle_statues.FAULT_INJECTED, bundle_statues.FAULT_INJECTED])
        elif target == "destroy_bundle":
            gen_mock_with_status_update(monkeypatch, [bundle_statues.DESTROYING, bundle_statues.DESTROYED])

    return mock_invoke_bundle


def test_evaluate_agent(monkeypatch):

    bundles = {
        "bundle1": True,
        "bundle2": False,
    }

    monkeypatch.setattr(BundleOperator, "invoke_bundle", gen_mock_invoke_bundle(monkeypatch))

    def mock_invoke_agent(self, bundle_operator: BundleOperator, bundle_entity: Dict[str, Any], output_dir: Path):
        monkeypatch.setattr(sys.modules[__name__], "get_evaluation", lambda: {"pass": bundles[bundle_operator.bundle.name], "report": []})

    monkeypatch.setattr(AgentOperator, "invoke_agent", mock_invoke_agent)

    bench_config = BenchConfig(title="test", is_test=True, soft_delete=False, resolution_wait=1)
    ao = AgentOperator(AgentInfo(id="test", name="agent1", directory="/tmp"))
    bos = [
        BundleOperator(
            bundle=Bundle(id="test", name=x, directory=".", incident_type="test", status=bundle_statues.INITIAL),
            bundle_request=BundleRequest(shared_workspace="/tmp/shared"),
        )
        for x in bundles.keys()
    ]
    bundle_results = []
    for bo in bos:
        bundle_results = bundle_results + Benchmark().evaluate(ao, bo, OUTPUT_DIR, bench_config)
    df = BundleResult.to_dataframe(bundle_results)
    df[BundleResult.Column.ttr] = df[BundleResult.Column.ttr].dt.total_seconds()
    assert not df[(df[BundleResult.Column.name] == "bundle1") & (df[BundleResult.Column.passed] == True)].empty
    assert not df[(df[BundleResult.Column.name] == "bundle2") & (df[BundleResult.Column.passed] == False)].empty


def test_benchmark(monkeypatch):

    bundle_map = {
        "bundle1": True,
        "bundle2": False,
    }

    agent_success_map = {
        "agent1": True,
        "agent2": False,
    }

    agents = [AgentInfo(id="test", name=x, directory=".") for x in agent_success_map.keys()]
    bundles = [Bundle(id="test", name=x, directory=".", incident_type="test", status=bundle_statues.INITIAL) for x in bundle_map.keys()]
    monkeypatch.setattr(BundleOperator, "invoke_bundle", gen_mock_invoke_bundle(monkeypatch))

    def mock_invoke_agent(self: AgentOperator, bundle_operator: BundleOperator, bundle_entity: Dict[str, Any], output_dir: Path):
        monkeypatch.setattr(
            sys.modules[__name__],
            "get_evaluation",
            lambda: {"pass": agent_success_map[self.agent_info.name] * bundle_map[bundle_operator.bundle.name], "report": []},
        )

    monkeypatch.setattr(AgentOperator, "invoke_agent", mock_invoke_agent)

    bench_config = BenchConfig(title="test", is_test=True, soft_delete=False, resolution_wait=1)
    bench_run_config = BenchRunConfig(
        benchmark_id="test", push_model=False, config=bench_config, agents=agents, bundles=bundles, output_dir=OUTPUT_DIR.as_posix()
    )
    benchmark_results = Benchmark().benchmark(bench_run_config)
    write_for_leaderboard(benchmark_results, OUTPUT_DIR)
