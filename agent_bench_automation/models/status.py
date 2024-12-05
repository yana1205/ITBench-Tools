from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Condition(BaseModel):
    lastTransitionTime: datetime = Field(..., description="The last time the condition transitioned from one status to another.")
    status: str = Field(..., description='The status of the condition: "True", "False", or "Unknown".')
    type: str = Field(..., description="The type of condition (e.g., 'Deployed', 'FaultInjected', 'Destroyed').")
    message: Optional[str] = Field(default=None, description="A human-readable message indicating details about the condition.")
    reason: Optional[str] = Field(default=None, description="A brief machine-readable explanation for the condition's status.")


class Status(BaseModel):
    conditions: List[Condition] = Field(..., description="List of conditions for the bundle.")
