from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from agent_bench_automation.app.models.base import Metadata, Status


class BenchmarkSpec(BaseModel):
    name: str
    runner_id: Optional[str] = None
    log_file_path: Optional[str] = None
    bundle_results_path: Optional[str] = None


class Benchmark(BaseModel):
    metadata: Metadata
    spec: BenchmarkSpec
    status: Optional[Status] = None


class AgentAssignment(BaseModel):
    bundle_id: str
    agent_id: str


class AgentStatus(Status):
    id: str
    name: str
    current_assignment: str


class BundleStatus(Status):
    id: str
    name: str
    assigned_agent_id: str


class BenchmarkStatus(BaseModel):
    id: str
    name: str
    creation_timestamp: datetime
    agent: AgentStatus
    bundles: List[BundleStatus]


class BenchmarkJobTake(BaseModel):
    runner_id: str
