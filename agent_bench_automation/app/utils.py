import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Request
from jose import jwt

from agent_bench_automation.app.config import (
    HASH_ALGORITHM,
    SECRET_KEY,
    TOKEN_SESSION_KEY,
    AppConfig,
    DefaultBundle,
)
from agent_bench_automation.app.models.base import Status
from agent_bench_automation.app.models.bundle import BundleSpec
from agent_bench_automation.app.models.user import TokenPayload


def get_tempdir(id: str):
    return f"/tmp/{id}"


def get_timestamp() -> datetime:
    return datetime.now(timezone.utc)


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
