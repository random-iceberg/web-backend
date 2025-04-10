from fastapi import APIRouter, HTTPException
from models.schemas import PassengerData, PredictionResult
from services.prediction_service import predict_survival

router = APIRouter()

@router.post("/", response_model=PredictionResult, summary="Predict Titanic survival")
async def predict(data: PassengerData):
    """
    Endpoint to predict the survival of a Titanic passenger.
    TODO: replace the heuristic logic with the ML inference call.
    """
    try:
        # Call the prediction service to compute the result.
        result = predict_survival(data)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
