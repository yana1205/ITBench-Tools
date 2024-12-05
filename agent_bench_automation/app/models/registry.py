from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from agent_bench_automation.app.models.agent import Agent, AgentAccessInfo, BundleAccessInfo
from agent_bench_automation.app.models.bundle import Bundle


class User(BaseModel):
    username: str
    id: str


class RegistryRequest(BaseModel):
    username: str
    user_id: str


class RegistryItem(BaseModel):
    name: str
    creation_timestamp: datetime
    bundles: List[Bundle] = []
    agents: List[Agent] = []


class BenchmarkRequest(BaseModel):
    name: str
    agent_id: str
    bundle_ids: List[str]


class BenchmarkInfo(BaseModel):
    id: str
    name: str
    token: str
    result_endpoint: str
    agent_access: Optional[AgentAccessInfo] = None
    bundle_accesses: Optional[List[BundleAccessInfo]] = None
    agents: Optional[List[Agent]] = None
    bundles: Optional[List[Bundle]] = None
    root_benchmark_id: Optional[str] = None
    root_agents: Optional[List[Agent]] = None
    root_bundles: Optional[List[Bundle]] = None
