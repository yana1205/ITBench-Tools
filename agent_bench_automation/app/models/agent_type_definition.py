from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AgentTypeDefinition(BaseModel):
    id: str = Field(..., description="The human readable unique identifier for the Agent type, e.g., 'SRE' or 'Compliance'.")
    allowed_levels: List[str] = Field(
        ..., description="A list of levels permitted for this Agent type, such as 'Beginner', 'Intermediate', or 'Expert'."
    )
    allowed_categories: List[str] = Field(
        ...,
        description="A list of scenario categories applicable to this Agent type, such as 'resource unavailability', 'saturation', or 'traffic' for SRE.",
    )
    allowed_complexities: List[str] = Field(
        ..., description="A list of scenario complexity levels suitable for this Agent type, such as 'Low', 'Medium', or 'High'."
    )
    level_to_complexities_map: Dict[str, List[str]] = Field(
        ..., description="A mapping of Agent levels to the corresponding scenario complexity levels."
    )
    category_to_task_map: Dict[str, Any] = Field(
        ..., description="A mapping of Agent category to the corresponding scenario tasks and sample json expected."
    )
    sampling_number: int = Field(..., description="The maximum number of sampled scenarios")
