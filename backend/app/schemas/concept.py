from pydantic import BaseModel, ConfigDict


class ConceptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str
    subject: str
    difficulty_level: int


class ConceptDependencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prerequisite_id: int
    dependent_id: int
    weight: float


class ConceptGraphRead(BaseModel):
    """Full graph payload shaped for direct consumption by React Flow
    (nodes + edges) on the frontend — built in Phase 2 once the seed
    data / graph-loading service exists."""

    nodes: list[ConceptRead]
    edges: list[ConceptDependencyRead]
