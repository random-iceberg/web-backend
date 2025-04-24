from pydantic import BaseModel, Field
from typing import Literal

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
    survived: bool
    probability: float