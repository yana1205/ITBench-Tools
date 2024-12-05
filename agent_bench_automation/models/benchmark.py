from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel, Field

from agent_bench_automation.models.agent import AgentInfo
from agent_bench_automation.models.bundle import Bundle, BundleResult


class BenchConfig(BaseModel):
    title: str
    is_test: bool
    soft_delete: bool
    resolution_wait: int = 30


class BenchRunConfig(BaseModel):
    benchmark_id: str = Field(..., description="Unique Identifier")
    push_model: bool = False
    config: BenchConfig
    agents: List[AgentInfo]
    bundles: List[Bundle]
    output_dir: str
    token: Optional[str]
    host: Optional[str]
    port: Optional[int]


class BenchmarkResult(BaseModel):
    name: str = Field(..., description="The name identifying the benchmark test.")
    incident_type: Optional[str] = Field(None, description="Incident types.")
    agent: str = Field(..., description="The name of Agent receiving the benchmark.")
    results: List[BundleResult] = Field(..., description="A list containing the results of the tested bundles.")
    mttr: timedelta = Field(..., description="Mean time to repair the issues for all bundles.")
    num_of_passed: int = Field(..., description="The number of passed bundle.")
    score: float = Field(..., description="The ratio of the number of passed bundle over total bundles.")
    date: datetime = Field(..., description="The date and time when the benchmark was performed.")

    class Column:
        name = "name"
        agent = "agent"
        incident_type = "incident_type"
        results = "results"
        mttr = "mttr"
        num_of_passed = "num_of_passed"
        score = "score"
        date = "date"

    @classmethod
    def to_dataframe(cls, results: List["BenchmarkResult"], exclude=[]) -> DataFrame:
        if len(results) > 0:
            _results = [{k: v for k, v in x.model_dump().items() if not k in exclude} for x in results]
        else:
            _results = pd.DataFrame(
                {
                    cls.Column.name: pd.Series(dtype="str"),
                    cls.Column.agent: pd.Series(dtype="str"),
                    cls.Column.incident_type: pd.Series(dtype="str"),
                    cls.Column.results: pd.Series(dtype="object"),
                    cls.Column.mttr: pd.Series(dtype="timedelta64[ns]"),
                    cls.Column.num_of_passed: pd.Series(dtype="float"),
                    cls.Column.score: pd.Series(dtype="float"),
                    cls.Column.date: pd.Series(dtype="datetime64[ns]"),
                }
            )
        return DataFrame(_results)
