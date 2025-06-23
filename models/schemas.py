from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PassengerData(BaseModel):
    """
    Data model representing input information for a Titanic passenger.
    - Define passenger fields (e.g., pclass, age, sex, etc.)"
    """

    age: float | None = Field(..., gt=0, description="Passenger's age")
    sibsp: int | None = Field(
        ..., ge=0, description="Number of siblings/spouses aboard"
    )
    parch: int | None = Field(
        ..., ge=0, description="Number of parents/children aboard"
    )
    fare: float | None = Field(..., ge=0, le=500)
    title: Literal["Master", "Miss", "Mr", "Mrs", "Rare"] | None
    passengerClass: Literal[1, 2, 3] | None = Field(
        ..., description="Class of the ticket (1st, 2nd, 3rd)"
    )
    sex: Literal["male", "female"] | None
    embarkationPort: Literal["C", "Q", "S"]
    wereAlone: bool | None
    cabinKnown: bool | None


class PredictionResult(BaseModel):
    """
    Data model for the result of a survival prediction
    - Define fields such as survived (bool) and probability (float).
    """

    survived: bool = Field(..., description="True if the passenger survived")
    probability: float = Field(..., description="Survival probability between 0 and 1")


class ModelBase(BaseModel):
    """Base model for ML model metadata."""

    algorithm: str
    name: str
    features: list[str]


class ModelCreate(ModelBase):
    """Payload for creating a new ML model."""

    pass


class ModelResponse(ModelBase):
    """Response model for ML model data."""

    id: str
    created_at: datetime
    accuracy: float | None = Field(None, description="Model accuracy, if available")


class TrainingResponse(BaseModel):
    """Response for model training requests."""

    job_id: str
    status: str
    message: str


class DeleteResponse(BaseModel):
    """Response for model deletion requests."""

    status: str
    message: str


class ErrorResponse(BaseModel):
    """Standardized error response schema for API endpoints"""

    detail: str
    code: str
    timestamp: datetime
    correlation_id: str

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}
