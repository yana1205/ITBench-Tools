# Copyright (c) 2024 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Any, Dict, Optional

import requests

from agent_bench_automation.app.models.base import AgentPhaseEnum
from agent_bench_automation.app.utils import create_status

logger = logging.getLogger(__name__)


class RestClient:
    def __init__(self, host: str, port: int, headers: Optional[Dict[str, str]] = None):
        self.base_url = f"http://{host}:{port}" if port > 0 else f"http://{host}"
        self.headers = headers
        if self.headers:
            self.headers["Content-type"] = "application/json"
        else:
            self.headers = {"Content-type": "application/json"}

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        _endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{_endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response

    def assign(self, benchmark_id: str, agent_id: str, bundle_id: str) -> requests.Response:
        url = f"{self.base_url}/benchmarks/{benchmark_id}/assign_agent"
        response = requests.put(url, headers=self.headers, json={"agent_id": agent_id, "bundle_id": bundle_id})
        return response

    def put(self, endpoint: str, body, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        _endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{_endpoint}"
        response = requests.put(
            url,
            headers=self.headers,
            data=body,
            params=params,
        )
        return response

    def post(self, endpoint: str, body, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        _endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{_endpoint}"
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

    def upload_file(self, benchmark_id: str, file_path: str, new_file_name: str):
        with open(file_path, "rb") as file:
            files = {"file": (new_file_name, file)}
            url = f"{self.base_url}/benchmarks/{benchmark_id}/file"
            response = requests.post(url, headers={"Authorization": self.headers["Authorization"]}, files=files)
            response.raise_for_status()
