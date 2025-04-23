from pydantic import BaseModel, Field

class PassengerData(BaseModel):
    """
    Data model representing input information for a Titanic passenger.
    
    TODO:
      - Define passenger fields (e.g., pclass, age, sex, etc.)"
    """
    pass

class PredictionResult(BaseModel):
    """
    Data model for the result of a survival prediction.
    
    TODO:
      - Define fields such as survived (bool) and probability (float).
    """
    survived: bool # TODO placeholder
