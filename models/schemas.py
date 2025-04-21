from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class PassengerData(BaseModel):
    """
    Data model representing input information for a Titanic passenger.
    
    TODO:
      - Define passenger fields (e.g., pclass, age, sex, etc.)"
    """
    pass # Default Placeholder, Information regarding Passenger Data structure needed

class PredictionResult(BaseModel):
    """
    Data model for the result of a survival prediction.
    
    TODO:
      - Define fields such as survived (bool) and probability (float).
    """
    pass # Default Placeholder, Information regarding Prediction Result structure needed

class ModelBase(BaseModel):
    """Base model for ML model data"""
    algorithm: str
    name: str
    features: List[str]

class ModelCreate(ModelBase):
    """Model data for creating a new ML model"""
    pass

class ModelResponse(ModelBase):
    """Response model for ML model data"""
    id: str
    created_at: datetime
    accuracy: Optional[float] = None

class TrainingResponse(BaseModel):
    """Response for model training request"""
    job_id: str
    status: str
    message: str

class DeleteResponse(BaseModel):
    """Response for model deletion request"""
    status: str
    message: str