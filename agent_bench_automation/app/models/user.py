from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from agent_bench_automation.app.models.base import Metadata, Status


class UserTypeEnum(str, Enum):
    User = "user"
    Agent = "agent"


class UserSpec(BaseModel):
    username: str
    hashed_password: str
    user_type: UserTypeEnum
    delegated_to: Optional[str] = ""


class User(BaseModel):
    metadata: Metadata
    spec: UserSpec
    status: Status


class UserCreation(BaseModel):
    username: str
    password: str


class UserCreationResponse(BaseModel):
    username: str
    id: str
    message: Optional[str] = ""


class TokenPayload(BaseModel):
    sub: str
    name: str
    user_type: UserTypeEnum
    delegated_id: Optional[str] = None
    exp: Optional[datetime] = None
