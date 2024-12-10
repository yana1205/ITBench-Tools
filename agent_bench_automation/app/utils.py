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

import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Request

from agent_bench_automation.app.config import (
    TOKEN_SESSION_KEY,
    AppConfig,
    DefaultBundle,
)
from agent_bench_automation.app.models.base import Status
from agent_bench_automation.app.models.bundle import BundleSpec
from agent_bench_automation.app.token_manager import TokenManager


def get_tempdir(id: str):
    return f"/tmp/{id}"


def get_timestamp() -> datetime:
    return datetime.now(timezone.utc)


def get_timestamp_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def create_status(phase: str, message: Optional[str] = None) -> Status:
    return Status(lastTransitionTime=get_timestamp(), phase=phase, message=message)


def load_default_bundles_from_file(app_config: AppConfig) -> List[DefaultBundle]:
    default_bundles: List[DefaultBundle] = []
    for db in app_config.default_bundles:
        default_bundle = DefaultBundle(bench_type=db.bench_type)
        bundles = db.bundles if db.bundles else []
        if db.path:
            with open(db.path, "r") as f:
                data = json.load(f)
                b = [BundleSpec.model_validate(x) for x in data]
                bundles = bundles + b
        default_bundle.bundles = bundles
        default_bundles.append(default_bundle)
    return default_bundles


def get_token_from_session(request: Request) -> Optional[str]:
    return request.session.get(TOKEN_SESSION_KEY)


def get_username_from_session(request: Request) -> Optional[str]:
    token_str = request.session.get(TOKEN_SESSION_KEY)
    token = TokenManager(verify=False).parse_token(token_str)
    return token.name
