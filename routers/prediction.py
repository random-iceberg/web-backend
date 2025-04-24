from fastapi import APIRouter, HTTPException, Request
from models.schemas import PassengerData, PredictionResult
from services.prediction_service import predict_survival
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=PredictionResult, summary="Predict Titanic Survival")
async def predict_passenger_survival(data: PassengerData, request: Request) -> PredictionResult:
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
    # Audit incoming request
    client_host = request.client.host if request.client else 'unknown'
    logger.info("Prediction request received", extra={
        "client_ip": client_host,
        "payload": data.model_dump()
    })

    try:
        # Delegate to service layer
        result: PredictionResult = predict_survival(data)

        # Log success
        logger.info("Prediction completed successfully", extra={
            "result": result.model_dump()
        })
        return result

    except ValueError as ve:
        # Service layer threw validation error
        logger.warning("Validation error during prediction", exc_info=ve)
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as exc:
        # Unexpected errors
        logger.error("Error during prediction", exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal Server Error")
