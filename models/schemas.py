from datetime import datetime
from typing import Dict, Literal, Union

from pydantic import BaseModel, Field, RootModel


class PassengerData(BaseModel):
    """
    Data model representing input information for a Titanic passenger.
    - Define passenger fields (e.g., pclass, age, sex, etc.)
    """

    age: float = Field(..., gt=0, description="Passenger's age")
    fare: float = Field(..., gt=0, description="Passenger's fare")
    sibsp: int = Field(..., ge=0, description="Number of siblings/spouses aboard")
    parch: int = Field(..., ge=0, description="Number of parents/children aboard")
    passengerClass: Literal[1, 2, 3] = Field(
        ..., description="Class of the ticket (1st, 2nd, 3rd)"
    )
    sex: Literal["male", "female"]
    embarkationPort: Literal["C", "Q", "S"]
    title: Literal["master", "miss", "mr", "mrs", "rare"]
    wereAlone: bool
    cabinKnown: bool
    model_ids: list[str] | None = None


class PredictionResult(BaseModel):
    """
    Data model for the result of a survival prediction
    - Define fields such as survived (bool) and probability (float).
    """

    survived: bool = Field(..., description="True if the passenger survived")
    probability: float = Field(..., description="Survival probability between 0 and 1")


class MultiModelPredictionResult(
    RootModel[Dict[str, Union[PredictionResult, Dict[str, str]]]]
):
    """
    Data model for aggregated prediction results from multiple models.
    Maps model_id to its PredictionResult or an error message.
    """

    pass


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
    created_at: datetime | None = Field(
        None, description="Timestamp of model creation, if available"
    )
    accuracy: float | None = Field(None, description="Model accuracy, if available")
    status: str = Field(
        "unknown", description="Current training status of the model"
    )  # New status field
    is_restricted: bool = Field(
        False, description="True if the model is restricted for anonymous users"
    )
    is_removable: bool = Field(default=True)


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
