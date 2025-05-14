from fastapi import APIRouter, HTTPException, Request
from models.schemas import PassengerData, PredictionResult
from services.prediction_service import predict_survival
from typing import List
from datetime import datetime
import logging
from pydantic import BaseModel


# Configure module-level logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=PredictionResult, summary="Predict Titanic Survival")
async def predict_passenger_survival(data: PassengerData) -> PredictionResult:
    """
    Endpoint to predict the survival of a Titanic passenger.

    - Validates input via Pydantic model PassengerData.
    - Forwards data to the prediction service.
    - Logs each request and result for auditing.

    Returns:
        PredictionResult: Contains 'survived' flag and 'probability'.

    Raises:
        HTTPException 400: Bad request with descriptive error message.
        HTTPException 500: Internal server error.
    """
    try:
        # Delegate to service layer
        result: PredictionResult = predict_survival(data)

        return result

    except ValueError as ve:
        # Service layer threw validation error
        logger.warning("Validation error during prediction", exc_info=ve)
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as exc:
        # Unexpected errors
        logger.error("Error during prediction", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal Server Error")


class PredictionHistory(BaseModel):
    timestamp: datetime
    input: PassengerData
    output: PredictionResult

@router.get("/history", 
    response_model=List[PredictionHistory],
    summary="Get Recent Predictions")
async def get_prediction_history(request: Request):
    """
    Retrieves the 10 most recent predictions for the authenticated user.

    Returns:
        List[PredictionHistory]: A list of prediction records containing timestamp,
                               input parameters and prediction results.
    """
    try:
        # Get database session from request state 
        db = request.state.async_session

        # Query last 10 predictions ordered by timestamp
        query = """
            SELECT timestamp, input_data, result 
            FROM predictions
            ORDER BY timestamp DESC 
            LIMIT 10
        """
        
        result = await db.execute(query)
        predictions = await result.fetchall()

        # Transform to response model
        history = [
            PredictionHistory(
                timestamp=row.timestamp,
                input=row.input_data,
                output=row.result
            )
            for row in predictions
        ]

        return history

    except Exception as exc:
        logger.error("Error retrieving prediction history: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve prediction history"
        )