import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError

from db.schemas import Prediction, User
from dependencies.auth import AnyRole, get_current_user
from models.schemas import MultiModelPredictionResult, PassengerData, PredictionResult
from services.prediction_service import predict_survival

# Configure module-level logger
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/", response_model=MultiModelPredictionResult, summary="Predict Titanic Survival"
)
async def predict_passenger_survival(
    data: PassengerData,
    request: Request,
    role: AnyRole,
    current_user: Annotated[User | None, Depends(get_current_user)],
) -> MultiModelPredictionResult:
    # Ensure model_ids is not empty if provided
    if data.model_ids is not None and not data.model_ids:
        raise HTTPException(
            status_code=400,
            detail="If 'model_ids' is provided, it cannot be an empty list.",
            headers={
                "X-Correlation-ID": getattr(request.state, "correlation_id", None)
            },
        )
    """
    Endpoint to predict the survival of a Titanic passenger.
    This now associates the prediction with the logged-in user.
    """
    correlation_id = getattr(request.state, "correlation_id", None)

    try:
        async_session = request.state.async_session  # This is a factory
        async with async_session() as db_session:  # Create a session instance
            results = await predict_survival(
                data, db_session, data.model_ids, current_user
            )
            return MultiModelPredictionResult.model_validate(results)

    except ValueError as ve:
        logger.warning("Validation error during prediction", exc_info=ve)
        raise HTTPException(
            status_code=400,
            detail=str(ve),
            headers={"X-Correlation-ID": correlation_id},
        )

    except Exception as exc:
        logger.error("Error during prediction", exc_info=exc)
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
            headers={"X-Correlation-ID": correlation_id},
        )


class PredictionHistory(BaseModel):
    timestamp: datetime
    input: PassengerData
    output: PredictionResult


@router.get(
    "/history",
    response_model=list[PredictionHistory],
    summary="Get Recent Predictions",
)
async def get_prediction_history(
    request: Request, current_user: Annotated[User | None, Depends(get_current_user)]
):
    """
    Retrieves the 10 most recent predictions for the authenticated user.
    """
    correlation_id = getattr(request.state, "correlation_id", None)
    
    if not current_user or current_user.role not in ["user", "admin"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        async_session = request.state.async_session
        async with async_session() as session:
            query = (
                select(Prediction)
                .where(Prediction.user_id == current_user.id)
                .order_by(desc(Prediction.created_at))
                .limit(10)
            )
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
            headers={"X-Correlation-ID": correlation_id},
        )
