from typing import List, Optional

from pydantic import BaseModel

from agent_bench_automation.app.models.base import Env, Metadata, Status
from agent_bench_automation.app.models.scenario import Scenario


class AgentAccessInfo(BaseModel):
    id: str
    name: str
    source_id: str
    status_endpoint: str


class BundleAccessInfo(BaseModel):
    id: str
    name: str
    source_id: str
    status_endpoint: str
    manifest_endpoint: str


class AgentBenchmarkEntry(BaseModel):
    benchmark_id: str
    agent_access_info: AgentAccessInfo
    bundle_access_infos: List[BundleAccessInfo]
    status: Status


class AgentManifest(BaseModel):
    token: Optional[str] = ""
    manifest_endpoint: Optional[str] = None
    benchmark_entries: List[AgentBenchmarkEntry] = []


class AgentSpec(BaseModel):
    name: str
    type: Optional[str] = None
    level: Optional[str] = None
    scenario_category: Optional[str] = None
    path: Optional[str] = None
    mode: Optional[str] = "remote"
    env: Optional[List[Env]] = None
    user_id: Optional[str] = None
    agent_manifest: Optional[AgentManifest] = None


class Agent(BaseModel):
    metadata: Metadata
    spec: AgentSpec
    status: Optional[Status] = None
