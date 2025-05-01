import httpx
from models.schemas import PassengerData, PredictionResult
import logging

logger = logging.getLogger(__name__)
MODEL_SERVICE_API = "http://model-api:8000/predict"

def predict_survival(data: PassengerData) -> PredictionResult:
    """
    Main entry for predicting survival:
      1. (Optionally) validate any domain-specific rules.
      2. Send payload to the external Model API.
      3. Format and return the prediction result.
    """
    # Domain-specific validation (beyond Pydantic)
    _validate_passenger_data(data)

    # Perform inference
    score: float = _inference_model_call(data)

    # Format into PredictionResult
    result: PredictionResult = _format_prediction_result(score)
    return result


def _validate_passenger_data(data: PassengerData) -> None:

    # Validates the passenger input data.

    if data.passengerClass not in [1, 2, 3]:
        raise ValueError("Invalid passenger class: must be 1, 2 or 3.")
    
    if data.sex.lower() not in ["male", "female"]:
        raise ValueError("Invalid sex: must be 'Male' or 'Female'")
    
    if not isinstance(data.age, (int, float)):
        raise ValueError("Invalid age: must be a number.")

    if data.age < 0 or data.age >= 120:
        raise ValueError("Invalid age: must be between 0 and 120.")

    if not isinstance(data.sibsp, int) or data.sibsp < 0:
        raise ValueError("Invalid sibsp: must be a non-negative integer.")
    
    if not isinstance(data.parch, int) or data.parch < 0:
        raise ValueError("Invalid parch: must be a non-negative integer.")
    
    if data.embarkation_port.upper() not in ["C", "Q", "S"]:
        raise ValueError("Invalid embarkation port: must be 'C', 'Q', or 'S'.")

    if not isinstance(data.is_alone, bool):
        raise ValueError("Invalid is_alone: must be a boolean.")

    if data.family_size != data.sibsp + data.parch + 1:
        raise ValueError("Invalid family_size: must equal sibsp + parch + 1.")

    if not isinstance(data.cabin_known, bool):
        raise ValueError("Invalid cabin_known: must be a boolean.")

def _inference_model_call(data: PassengerData) -> float:
    """
    Calls the ML inference module or external service to get the prediction score.

    TODO:
      - Construct the inference request.
      - Handle the API call and response from the ML model service.
    """
    payload = data.model_dump()
    try:
        response = httpx.post(MODEL_SERVICE_API, json=payload, timeout=5.0)
        response.raise_for_status()
        body = response.json()

    except httpx.Timeout as e:
        logger.error(f"Model API request timed out after {e.request_timeout} seconds: {e}")

    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Model API: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Model API returned HTTP {e.response.status_code}: {e.response.text}")

    # Expect the response to contain a 'probability' key
    if 'probability' not in body:
        logger.error(f"Malformed response from Model API: {body}")

    try:
        return float(body['probability'])
    except (TypeError, ValueError):
        logger.error(f"Invalid probability value: {body['probability']}")



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
