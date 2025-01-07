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

import os
from typing import List, Optional

from pydantic import BaseModel, Field

from agent_bench_automation.app.models.agent_type_definition import AgentTypeDefinition
from agent_bench_automation.app.models.bundle import BundleSpec
from agent_bench_automation.app.storage.config import StorageConfig

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_MINIBENCH_HOST = "127.0.0.1"
DEFAULT_MINIBENCH_PORT = 8001
DEFAULT_MINIBENCH_TIMEOUT_SECONDS = 600

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tmp4now")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "tmp4nowsession")
TOKEN_SESSION_KEY = os.getenv("TOKEN_SESSION_KEY", "tmp4now")
LEADERBOARD_SESSION_KEY = "leaderboard"
HASH_ALGORITHM = "HS256"
TOKEN_EXPIRATION_MINUTES = 60

BASE_RESOURCE_REF_LABEL = "reference_id"
ROOT_BENCHMARK_LABEL = "root"
BENCHMARK_RESOURCE_ROOT = "_system"

ROOT_PATH = os.getenv("ROOT_PATH", "")
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "")
PROJECT_LOG_LEVEL = os.getenv("PROJECT_LOG_LEVEL", "")
ROOT_LOG_LEVEL = os.getenv("ROOT_LOG_LEVEL", "")


class DefaultBundle(BaseModel):
    bench_type: str = Field(..., description="Benchmark Type")
    path: str = Field(None, description="Path to the bundles.json file. Used to load scenarios if the 'bundles' field is not provided.")
    bundles: List[BundleSpec] = Field(
        None,
        description="List of bundles. If this field is defined, it takes precedence over the 'path' field, and the specified bundles will be used directly.",
    )


class ServiceAccount(BaseModel):
    id: str
    type: str


class AppConfig(BaseModel):
    host: Optional[str] = Field(DEFAULT_HOST, description="Host to bind the server. Default is 127.0.0.1.")
    port: Optional[int] = Field(DEFAULT_PORT, description="Port to bind the server. Default is 8000.")
    storage_config: StorageConfig
    default_bundles: Optional[List[DefaultBundle]] = Field([], description="Default bundles")
    enable_auth: Optional[bool] = False
    enable_soft_delete: Optional[bool] = Field(False, description="Specifies whether to enable soft-delete (invoke Make revert).")
    token: Optional[str] = None
    default_agent_types: Optional[List[AgentTypeDefinition]] = Field([], description="Default Agent Type Definitions")
    polling_interval: Optional[int] = Field(None, description="Seconds for polling interval.")
    service_accounts: Optional[List[ServiceAccount]] = None
    admin_user: Optional[str] = "admin"
    admin_pass: Optional[str] = "admin"
    ssl_enabled: Optional[bool] = Field(False, description="Enable or disable SSL. Set to True to enable SSL for the server.")
    ssl_verify: Optional[bool] = Field(
        False,
        description="Enable or disable SSL certificate verification. Set to True to verify the certificate, or False to disable verification (default: False).",
    )
    ssl_auto_gen: Optional[bool] = Field(
        False,
        description="Enable automatic generation of a self-signed SSL certificate. If True, a certificate will be generated dynamically.",
    )
    ssl_auto_gen_dir: Optional[str] = Field(
        None,
        description="Directory path to save the automatically generated SSL certificate and key. Required if `ssl_auto_cert_gen` is True.",
    )
    ssl_auto_gen_common_name: Optional[str] = Field(
        "localhost",
        description="Common Name (CN) for the generated SSL certificate. Used as the hostname in the certificate. If not specified, defaults to 'localhost'.",
    )
    ssl_cert_file: Optional[str] = Field(
        None, description="Path to the SSL certificate file. Required if SSL is enabled and not using auto-generated certificates."
    )
    ssl_key_file: Optional[str] = Field(
        None, description="Path to the SSL key file. Required if SSL is enabled and not using auto-generated certificates."
    )
