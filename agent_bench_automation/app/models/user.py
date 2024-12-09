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
