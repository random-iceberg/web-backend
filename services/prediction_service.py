import os
import httpx
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from typing import Dict
from db.schemas import Prediction
from models.schemas import PassengerData, PredictionResult
from services.model_service import get_all_models

# TODO: remove httpx, do over the network container yapping #
logger = logging.getLogger(__name__)
MODEL_SERVICE_API = ""


async def predict_survival(
    data: PassengerData, db_session: AsyncSession, model_id: str | None = None
) -> PredictionResult:
    """
    Main entry for predicting survival and storing the result:
      1. (Optionally) validate any domain-specific rules.
      2. Send payload to the external Model API.
      3. Store prediction in database.
      4. Format and return the prediction result.
    """
    MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8000")

    async with httpx.AsyncClient() as client:
        models_response = await client.get(f"{MODEL_SERVICE_URL}/models/")
        models_response.raise_for_status()
        model_id = models_response.json()[0][
            "id"
        ]  # TODO: change how model_id is determined

    # Domain-specific validation (beyond Pydantic)
    await _validate_passenger_data(data)

    # Perform inference
    response: float = await _inference_model_call(data, db_session, model_id)

    # Format into PredictionResult
    result: PredictionResult = _format_prediction_result(response)

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


async def _inference_model_call(
    data: PassengerData, db_session: AsyncSession, model_id: str
) -> Dict:
    """
    TODO: change this behavior later.
    """
    MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8000")

    async with httpx.AsyncClient() as client:
        # TODO: massive TODO, fix the manual remapping
        embarked_mapping = {"C": "cherbourg", "Q": "queenstown", "S": "southhampton"}
        input = {
            "pclass": data.passengerClass,
            "sex": data.sex,
            "age": data.age,
            "fare": "200",
            "travelled_alone": data.wereAlone,
            "embarked": embarked_mapping[data.embarkationPort],
            "title": "mr",
        }

        predict_response = await client.post(
            f"{MODEL_SERVICE_URL}/models/{model_id}/predict", json=input
        )
        predict_response.raise_for_status()
        return {
            "survived": predict_response.json()["survived"],
            "probability": predict_response.json()["probability"],
        }


def _format_prediction_result(response: Dict) -> PredictionResult:
    """
    Formats the raw inference score into a structured PredictionResult.
    """
    survived, probability = response["survived"], response["probability"]
    return PredictionResult(survived=survived, probability=probability)
