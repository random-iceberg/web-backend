from pydantic import BaseModel, Field

class PassengerData(BaseModel):
    pclass: int = Field(..., example=3, description="Passenger Class (1 = 1st, 2 = 2nd, 3 = 3rd)")
    sex: str = Field(..., example="male", description="Gender of the passenger")
    age: float = Field(..., example=22.0, description="Passenger age")
    sibsp: int = Field(..., example=1, description="Number of siblings/spouses aboard")
    parch: int = Field(..., example=0, description="Number of parents/children aboard")
    fare: float = Field(..., example=7.25, description="Ticket fare")
    embarked: str = Field(..., example="S", description="Port of embarkation (C, Q, or S)")

class PredictionResult(BaseModel):
    survived: bool = Field(..., example=True, description="Prediction outcome: True if survived, otherwise False")
    probability: float = Field(..., example=0.85, description="Predicted probability of survival")
