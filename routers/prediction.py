import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError

from db.schemas import Prediction
from models.schemas import PassengerData, PredictionResult
from services.prediction_service import predict_survival

# Configure module-level logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=PredictionResult, summary="Predict Titanic Survival")
async def predict_passenger_survival(
    data: PassengerData, request: Request
) -> PredictionResult:
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
        async_session = request.state.async_session  # This is a factory
        async with async_session() as db_session:  # Create a session instance
            result = await predict_survival(data, db_session)
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


@router.get(
    "/history",
    response_model=list[PredictionHistory],
    summary="Get Recent Predictions",
)
async def get_prediction_history(request: Request):
    """
    Retrieves the 10 most recent predictions for the authenticated user.

    Returns:
        List[PredictionHistory]: A list of prediction records containing timestamp,
                               input parameters and prediction results.
    """
    try:
        async_session = request.state.async_session
        async with async_session() as session:
            query = select(Prediction).order_by(desc(Prediction.created_at)).limit(10)
            result = await session.execute(query)
            predictions = result.scalars().all()

            history = [
                PredictionHistory(
                    timestamp=p.created_at, input=p.input_data, output=p.result
                )
                for p in predictions
            ]
            return history

    except SQLAlchemyError as e:
        logger.error("Database error fetching history: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Database error occurred while fetching history: {str(e)}",
        )
