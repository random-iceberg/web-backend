from fastapi import APIRouter, HTTPException
from models.schemas import PassengerData, PredictionResult
from services.prediction_service import predict_survival
import logging
import json

router = APIRouter()

@router.post("/", response_model=PredictionResult, summary="Predict Titanic Survival")
async def predict_passenger_survival(data: PassengerData) -> PredictionResult:
    """
    Endpoint to predict the survival of a Titanic passenger.
    
    TODO:
      - Replace placeholder logic with actual integration with the ML inference service.
      - Add logging and enhanced error handling as needed.
    """
    logging.basicConfig(level=logging.ERROR)

# Data parsing failure (missing or invalid data)
    try:
        data_validation = json.load(data)

        REQUIRED_FIELDS = [
            "age",
            "sibsp",
            "parch",
            "passengerClass",
            "sex",
            "embarkationPort",
            "wereAlone",
            "cabinKnown"
        ]

        for field in REQUIRED_FIELDS:
            if data_validation[field] is None:
                raise KeyError()

    except Exception as exc:
        raise HTTPException(status_code=400, detail="Missing or Invalid Data")

    try:
        result = predict_survival(data)
        return result
    except Exception as exc:
        # TODO: Enhance with proper logging and error response details.
        raise HTTPException(status_code=500, detail="Internal Server Error")
