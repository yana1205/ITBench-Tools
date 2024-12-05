from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    id: str = Field(..., description="Unique Identifier")
    name: str = Field(..., description="The name of Agent.")
    directory: str = Field(..., description="The directory path of the Agent.")
    description: Optional[str] = Field(None, description="The description of the Agent.")
    mode: Optional[str] = Field(None, description="If Agent is owned and managed by Benchmark, select Local. Else, Remote. Default Local.")

    def get_path(self) -> Path:
        return Path(self.directory)
