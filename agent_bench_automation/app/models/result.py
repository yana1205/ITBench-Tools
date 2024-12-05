from typing import List, Optional

from pydantic import BaseModel

from agent_bench_automation.app.models.base import Env, Metadata, Status
from agent_bench_automation.models.bundle import BundleResult


class ResultSpec(BundleResult):
    bundle_id: str


class Result(BaseModel):
    metadata: Metadata
    spec: ResultSpec
    status: Optional[Status] = None
