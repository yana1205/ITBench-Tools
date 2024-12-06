from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from agent_bench_automation.app.models.base import Metadata, Status


class ScenarioSpec(BaseModel):
    type: str = Field(..., description="The type of scenario, e.g., 'SRE', 'FinOps', 'Compliance'.")
    name: str = Field(..., description="The name of the scenario, providing a human-readable identifier.")
    description: str = Field(..., description="A brief explanation of what the scenario entails.")
    complexity: str = Field(..., description="The complexity level of the scenario, e.g., 'Low', 'Medium', or 'High'.")
    category: str = Field(..., description="The category of the scenario, e.g., 'resource unavailability', 'saturation', 'traffic' for SRE.")
    scenario_class: str = Field(..., alias="class", description="The class or classification of the scenario, e.g. 'rhel9 CIS', 'kubernetes CIS'.")
    instance_id: str = Field(..., description="A unique identifier for the specific instance (bundle id) of the scenario.")
    model_config = ConfigDict(populate_by_name=True)


class Scenario(BaseModel):
    metadata: Metadata
    spec: ScenarioSpec
    status: Optional[Status] = None
