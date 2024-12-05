import logging
from typing import Any, Dict, Optional

import requests

from agent_bench_automation.app.models.base import AgentPhaseEnum
from agent_bench_automation.app.utils import create_status

logger = logging.getLogger(__name__)


class RestClient:
    def __init__(self, host: str, port: int, headers: Optional[Dict[str, str]] = None):
        self.base_url = f"http://{host}:{port}"
        self.headers = headers
        if self.headers:
            self.headers["Content-type"] = "application/json"
        else:
            self.headers = {"Content-type": "application/json"}

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response

    def assign(self, benchmark_id: str, agent_id: str, bundle_id: str) -> requests.Response:
        url = f"{self.base_url}/benchmarks/{benchmark_id}/assign_agent"
        response = requests.put(url, headers=self.headers, json={"agent_id": agent_id, "bundle_id": bundle_id})
        return response

    def put(self, endpoint: str, body, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}/{endpoint}"
        response = requests.put(
            url,
            headers=self.headers,
            data=body,
            params=params,
        )
        return response

    def post(self, endpoint: str, body, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(
            url,
            headers=self.headers,
            data=body,
            params=params,
        )
        return response

    def push_agent_status(self, benchmark_id: str, agent_id: str, phase: AgentPhaseEnum, message: Optional[str] = None):
        url = f"{self.base_url}/benchmarks/{benchmark_id}/agents/{agent_id}/status"
        status = create_status(phase.value, message)
        requests.put(url, headers=self.headers, data=status.model_dump_json())
