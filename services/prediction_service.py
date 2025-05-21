import logging

from sqlalchemy.ext.asyncio import AsyncSession

from db.schemas import Prediction
from models.schemas import PassengerData, PredictionResult

# TODO: remove httpx, do over the network container yapping #
logger = logging.getLogger(__name__)
MODEL_SERVICE_API = ""


async def predict_survival(
    data: PassengerData, db_session: AsyncSession
) -> PredictionResult:
    """
    Main entry for predicting survival and storing the result:
      1. (Optionally) validate any domain-specific rules.
      2. Send payload to the external Model API.
      3. Store prediction in database.
      4. Format and return the prediction result.
    """
    # Domain-specific validation (beyond Pydantic)
    await _validate_passenger_data(data)

    # Perform inference
    score: float = _inference_model_call(data)

    # Format into PredictionResult
    result: PredictionResult = _format_prediction_result(score)

    # Store prediction in database
    new_prediction = Prediction(
        input_data=data.model_dump(), result=result.model_dump()
    )
    db_session.add(new_prediction)
    await db_session.commit()

    return result


# TODO: mock response about invalid data
async def _validate_passenger_data(data: PassengerData) -> None:
    if data.passengerClass not in [1, 2, 3]:
        raise ValueError("Invalid passenger class: must be 1, 2 or 3.")

    if data.sex.lower() not in ["male", "female"]:
        raise ValueError("Invalid sex: must be 'male' or 'female'")

    if not isinstance(data.age, (int, float)):
        raise ValueError("Invalid age: must be a number.")

    if data.age < 0 or data.age >= 120:
        raise ValueError("Invalid age: must be between 0 and 120.")

    if not isinstance(data.sibsp, int) or data.sibsp < 0:
        raise ValueError("Invalid sibsp: must be a non-negative integer.")

    if not isinstance(data.parch, int) or data.parch < 0:
        raise ValueError("Invalid parch: must be a non-negative integer.")

    if data.embarkationPort.upper() not in ["C", "Q", "S"]:
        raise ValueError("Invalid embarkation port: must be 'C', 'Q', or 'S'.")

    if not isinstance(data.wereAlone, bool):
        raise ValueError("Invalid wereAlone: must be a boolean.")

    if not isinstance(data.cabinKnown, bool):
        raise ValueError("Invalid cabinKnown: must be a boolean.")

    return None


def _inference_model_call(data: PassengerData) -> float:
    # TODO: add call to MODEL_SERVICE_API
    # TODO: add error handling for post request
    # TODO: add handling for the returned data

    return 0.85


def _format_prediction_result(score: float) -> PredictionResult:
    """
    Formats the raw inference score into a structured PredictionResult.

    TODO:
      - Map the raw score to a boolean survival outcome.
      - Populate additional fields (such as prediction probability).
    """
    if not (0.0 <= score <= 1.0):
        logger.error(f"Invalid score: {score}. Must be between 0 and 1.")

    survived = score >= 0.5
    return PredictionResult(survived=survived, probability=score)
