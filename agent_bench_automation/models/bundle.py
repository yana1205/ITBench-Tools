from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel, Field

from agent_bench_automation.app.models.base import Env
from agent_bench_automation.app.models.bundle import MakeTargetMapping
from agent_bench_automation.models.status import Condition


class BundleCondition(Condition):
    lastProbeTime: Optional[datetime] = Field(default=None, description="The last time the condition was probed.")


class BundleStatus(BaseModel):
    kubeconfig: Optional[str] = Field(None, description="JSON Stringified kubeconfig.")
    conditions: List[BundleCondition] = Field(..., description="List of conditions for the bundle.")


class BundleInfo(BaseModel):
    name: str = Field(..., description="The name of the bundle.")
    description: Optional[str] = Field(None, description="The description of the bundle.")
    incident_type: Optional[str] = Field(None, description="The type of incident (any name is allowed).")


class BundleEvaluationError(BaseModel):
    code: str = Field(..., description="An error code representing the specific error type.")
    message: str = Field(..., description="A detailed error message explaining the nature of the error.")


class BundleEvaluation(BaseModel):
    pass_: bool = Field(..., description="Indicates whether the evaluation was successful (True) or failed (False).", alias="pass")
    details: Optional[str] = Field(None, description="Details related to the evaluation result.")
    errors: Optional[List[BundleEvaluationError]] = Field(
        None, description="A list of evaluation errors, if any, each containing an error code and message."
    )
    report: Optional[str] = Field("")


class Bundle(BundleInfo):
    id: str = Field(..., description="Unique identifier")
    directory: str = Field(..., description="The directory path of the bundle.")
    bundle_ready_timeout: Optional[int] = Field(
        300, description="Maximum time in seconds to wait for the scenario to become ready and an agent to be assigned."
    )
    agent_operation_timeout: Optional[int] = Field(
        300, description="Maximum time in seconds to wait for the agent to complete the operation after being assigned."
    )
    status: Optional[BundleStatus] = Field(None, description="Bundle status")
    input: Optional[Dict[str, Any]] = Field(
        None, description="The content of the input file represented as a dictionary with keys as strings and values as any type"
    )

    params: Optional[Dict[str, str]] = Field(None, description="Paramaters to be passed to Make invocation.")
    env: Optional[List[Env]] = None
    make_target_mapping: Optional[MakeTargetMapping] = None
    enable_evaluation_wait: Optional[bool] = Field(False)

    def get_path(self) -> Path:
        return Path(self.directory)


class BundleRequest(BaseModel):
    shared_workspace: str = Field(..., description="Shared workspace between bundle and agent.")
    input_file: Optional[str] = Field(None, description="Path to input file for 'make target INPUT_FILE=input_filr'.")


class BundleResult(BundleInfo):
    agent: str = Field(..., description="The name of the agent.")
    passed: bool = Field(..., description="True if an issue in the bundle was resolved.")
    ttr: timedelta = Field(..., description="Time to repair the issue.")
    errored: bool = Field(False, description="True if an error happened.")
    message: Optional[str] = Field(None, description="Any message.")
    date: datetime = Field(..., description="The date and time when the benchmark was performed.")

    class Column:
        agent = "agent"
        name = "name"
        incident_type = "incident_type"
        description = "description"
        passed = "passed"
        ttr = "ttr"
        errored = "errored"
        message = "message"
        date = "date"

    @classmethod
    def to_dataframe(cls, results: List["BundleResult"]) -> DataFrame:
        if len(results) > 0:
            _results = [x.model_dump() for x in results]
        else:
            _results = pd.DataFrame(
                {
                    cls.Column.agent: pd.Series(dtype="str"),
                    cls.Column.name: pd.Series(dtype="str"),
                    cls.Column.incident_type: pd.Series(dtype="str"),
                    cls.Column.description: pd.Series(dtype="str"),
                    cls.Column.passed: pd.Series(dtype="bool"),
                    cls.Column.ttr: pd.Series(dtype="timedelta64[ns]"),
                    cls.Column.errored: pd.Series(dtype="bool"),
                    cls.Column.message: pd.Series(dtype="str"),
                    cls.Column.date: pd.Series(dtype="datetime64[ns]"),
                }
            )
        return DataFrame(_results)
