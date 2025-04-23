from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PassengerData(BaseModel):
    """
    Data model representing input information for a Titanic passenger.

    TODO:
      - Define passenger fields (e.g., pclass, age, sex, etc.)
    """
    pass


class PredictionResult(BaseModel):
    """
    Data model for the result of a survival prediction.

    Fields:
      - survived: bool indicating whether the passenger survived
      - probability: float probability of survival (0.0 to 1.0)
    """
    survived: bool = Field(..., description="True if the passenger survived")
    probability: float = Field(..., description="Survival probability between 0 and 1")


class ModelBase(BaseModel):
    """Base model for ML model metadata."""
    algorithm: str
    name: str
    features: List[str]


class ModelCreate(ModelBase):
    """Payload for creating a new ML model."""
    pass


class ModelResponse(ModelBase):
    """Response model for ML model data."""
    id: str
    created_at: datetime
    accuracy: Optional[float] = Field(
        None, description="Model accuracy, if available"
    )


class TrainingResponse(BaseModel):
    """Response for model training requests."""
    job_id: str
    status: str
    message: str


class DeleteResponse(BaseModel):
    """Response for model deletion requests."""
    status: str
    message: str
