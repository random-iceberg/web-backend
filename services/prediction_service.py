import asyncio
import logging
import os
from typing import Dict, List, Union

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from db.schemas import Prediction
from models.schemas import PassengerData, PredictionResult

logger = logging.getLogger(__name__)
MODEL_SERVICE_API = ""


async def predict_survival(
    data: PassengerData, db_session: AsyncSession, model_ids: List[str] | None = None
) -> Dict[str, Union[PredictionResult, Dict]]:
    """
    Main entry for predicting survival and storing the result for multiple models:
      1. (Optionally) validate any domain-specific rules.
      2. Send payload to the external Model API for each selected model in parallel.
      3. Store prediction in database (for the first successful prediction, or consider storing all).
      4. Aggregate and return the prediction results for each model.
    """
    MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8000")

    # Domain-specific validation (beyond Pydantic)
    await _validate_passenger_data(data)

    results: Dict[str, Union[PredictionResult, Dict]] = {}
    tasks = []

    if not model_ids:
        # If no model_ids provided, fetching all models and using the first one (fallback)
        async with httpx.AsyncClient() as client:
            try:
                models_response = await client.get(f"{MODEL_SERVICE_URL}/models/")
                models_response.raise_for_status()
                all_models = models_response.json()
                if all_models:
                    model_ids = [all_models[0]["id"]]
                else:
                    raise ValueError("No models available for prediction.")
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to fetch models from service: {e}")
                raise ValueError("Failed to retrieve available models.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while fetching models: {e}")
                raise ValueError("An unexpected error occurred.")

    for model_id in model_ids:
        tasks.append(_inference_model_call(data, db_session, model_id))

    predictions = await asyncio.gather(*tasks, return_exceptions=True)

    for i, model_id in enumerate(model_ids):
        prediction_response = predictions[i]
        if isinstance(prediction_response, Exception):
            logger.error(
                f"Prediction failed for model {model_id}: {prediction_response}"
            )
            results[model_id] = {"error": str(prediction_response)}
        else:
            result: PredictionResult = _format_prediction_result(prediction_response)
            results[model_id] = result
            # Store prediction in database (only the first successful one)
            if isinstance(result, PredictionResult):
                new_prediction = Prediction(
                    input_data=data.model_dump(), result=result.model_dump()
                )
                db_session.add(new_prediction)
                await (
                    db_session.commit()
                )  # Committing after each prediction for now, considering batching

    return results


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
    Calls the external model service for prediction.
    """
    MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8000")

    async with httpx.AsyncClient() as client:
        embarked_mapping = {"C": "cherbourg", "Q": "queenstown", "S": "southhampton"}
        input_data = {
            "pclass": data.passengerClass,
            "sex": data.sex,
            "age": data.age,
            "fare": data.fare,
            "travelled_alone": data.wereAlone,
            "embarked": embarked_mapping[data.embarkationPort],
            "title": data.title,
        }

        predict_response = await client.post(
            f"{MODEL_SERVICE_URL}/models/{model_id}/predict", json=input_data
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
