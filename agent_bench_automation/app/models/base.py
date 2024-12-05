from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, TypeVar

from pydantic import BaseModel, Field


class BenchmarkPhaseEnum(str, Enum):
    NotStarted = "NotStarted"
    Running = "Running"
    Finished = "Finished"
    Error = "Error"


class BundlePhaseEnum(str, Enum):
    NotStarted = "NotStarted"
    Provisioning = "Provisioning"
    Provisioned = "Provisioned"
    FaultInjecting = "FaultInjecting"
    FaultInjected = "FaultInjected"
    Ready = "Ready"
    Evaluating = "Evaluating"
    Evaluated = "Evaluated"
    Terminating = "Terminating"
    Terminated = "Terminated"
    Error = "Error"


class AgentPhaseEnum(str, Enum):
    NotStarted = "NotStarted"
    Initializing = "Initializing"
    Ready = "Ready"
    Executing = "Executing"
    Finished = "Finished"
    Error = "Error"
    TimeedOut = "TimedOut"
    Terminating = "Terminating"
    Terminated = "Terminated"


class Metadata(BaseModel):
    id: str
    resource_type: str
    creation_timestamp: datetime
    labels: Optional[Dict[str, str]] = None
    user_id: Optional[str] = None


class Env(BaseModel):
    name: str
    value: str


def get_timestamp():
    return datetime.now(timezone.utc)


class Status(BaseModel):
    lastTransitionTime: Optional[datetime] = Field(
        default_factory=get_timestamp, description="The last time the condition transitioned from one status to another."
    )
    phase: str = Field(..., description="The phase of the condition.")
    message: Optional[str] = Field(default=None, description="A human-readable message indicating details about the condition.")


class Identifiable(BaseModel):
    metadata: Metadata


T = TypeVar("T", bound=Identifiable)
