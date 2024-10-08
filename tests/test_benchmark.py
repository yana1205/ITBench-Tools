import json
import sys

from caa_bench.agent_operator import AgentOperator
from caa_bench.benchmark import benchmark, evaluate_agent
from caa_bench.bundle_operator import BundleOperator
from caa_bench.models.agent import AgentInfo
from caa_bench.models.benchmark import BenchmarkResult
from caa_bench.models.bundle import Bundle, BundleResult, BundleStatus
from tests import bundle_statues


def get_status() -> BundleStatus:
    pass


def get_evaluation():
    pass


def gen_mock_with_status_update(monkeypatch, bundle_statuses):
    results = iter(bundle_statuses)
    mock_get_bundle_status = lambda: next(results)
    monkeypatch.setattr(sys.modules[__name__], "get_status", mock_get_bundle_status)


def gen_mock_invoke_bundle(monkeypatch):

    def mock_invoke_bundle(self, target, extra_args=[]):
        if target == "get_status":
            status_json = get_status().model_dump_json()
            data = {"status": json.loads(status_json)}
            return json.dumps(data)
        elif target == "evaluate":
            return json.dumps(get_evaluation())
        elif target == "deploy_bundle":
            gen_mock_with_status_update(monkeypatch, [bundle_statues.DEPLOYING, bundle_statues.DEPLOYED])
        elif target == "inject_fault":
            monkeypatch.setattr(sys.modules[__name__], "get_evaluation", lambda: {"pass": False, "report": []})
            gen_mock_with_status_update(monkeypatch, [bundle_statues.FAULT_INJECTING, bundle_statues.FAULT_INJECTED, bundle_statues.FAULT_INJECTED])
        elif target == "destroy_bundle":
            gen_mock_with_status_update(monkeypatch, [bundle_statues.DESTROYING, bundle_statues.DESTROYED])

    return mock_invoke_bundle


def test_benchmark(monkeypatch):

    agent_success_map = {
        "agent1": True,
        "agent2": False,
    }

    agents = [AgentInfo(name=x, directory=".") for x in agent_success_map.keys()]
    bundles = [Bundle(name="bundle", directory=".", status=bundle_statues.INITIAL)]
    monkeypatch.setattr(BundleOperator, "invoke_bundle", gen_mock_invoke_bundle(monkeypatch))

    def mock_invoke_agent(self: AgentOperator, bundle_operator: BundleOperator, kubeconfig: str, report: str):
        monkeypatch.setattr(sys.modules[__name__], "get_evaluation", lambda: {"pass": agent_success_map[self.agent_info.name], "report": []})

    monkeypatch.setattr(AgentOperator, "invoke_agent", mock_invoke_agent)

    benchmark_results = benchmark("test", agents, bundles, False, False)

    df = BenchmarkResult.to_dataframe(benchmark_results, exclude=[BenchmarkResult.Column.results])
    pass


def test_evaluate_agent(monkeypatch):

    bundles = {
        "bundle1": True,
        "bundle2": False,
    }

    monkeypatch.setattr(BundleOperator, "invoke_bundle", gen_mock_invoke_bundle(monkeypatch))

    def mock_invoke_agent(self, bundle_operator: BundleOperator, kubeconfig: str, report: str):
        monkeypatch.setattr(sys.modules[__name__], "get_evaluation", lambda: {"pass": bundles[bundle_operator.bundle.name], "report": []})

    monkeypatch.setattr(AgentOperator, "invoke_agent", mock_invoke_agent)

    bundle_results = evaluate_agent(
        AgentInfo(name="agent1", directory="/tmp"),
        [Bundle(name=x, directory=".", status=bundle_statues.INITIAL) for x in bundles.keys()],
        is_test=False,
        soft_delete=False,
    )
    df = BundleResult.to_dataframe(bundle_results)
    df[BundleResult.Column.ttr] = df[BundleResult.Column.ttr].dt.total_seconds()
    assert not df[(df[BundleResult.Column.name] == "bundle1") & (df[BundleResult.Column.passed] == True)].empty
    assert not df[(df[BundleResult.Column.name] == "bundle2") & (df[BundleResult.Column.passed] == False) & (df[BundleResult.Column.ttr] > 10)].empty
