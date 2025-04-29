from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime

class PassengerData(BaseModel):
    """
    Data model representing input information for a Titanic passenger.
   - Define passenger fields (e.g., pclass, age, sex, etc.)"
    """
    age: float = Field(..., gt=0, description="Passenger's age")
    sibsp: int = Field(..., ge=0, description="Number of siblings/spouses aboard")
    parch: int = Field(..., ge=0, description="Number of parents/children aboard")
    passengerClass: Literal[1, 2, 3] = Field(..., description="Class of the ticket (1st, 2nd, 3rd)")
    sex: Literal["male", "female"]
    embarkationPort: Literal["C", "Q", "S"]
    wereAlone: bool
    cabinKnown: bool


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
    features: List[str]


class ModelCreate(ModelBase):
    """Payload for creating a new ML model."""

    pass


class ModelResponse(ModelBase):
    """Response model for ML model data."""

    id: str
    created_at: datetime
    accuracy: Optional[float] = Field(None, description="Model accuracy, if available")


class TrainingResponse(BaseModel):
    """Response for model training requests."""

    job_id: str
    status: str
    message: str


class DeleteResponse(BaseModel):
    """Response for model deletion requests."""

    status: str
    message: str
