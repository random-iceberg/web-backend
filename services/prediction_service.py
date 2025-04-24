import os
import httpx
from models.schemas import PassengerData, PredictionResult

# URL of the external ML inference service
MODEL_API_URL = os.getenv("MODEL_API_URL", "http://localhost:8001/predict")


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
    """
    Perform any additional validation not covered by Pydantic models.
    Raise ValueError on any rule violation.
    """
    # Example: enforce realistic passenger age
    if data.age <= 0 or data.age > 120:
        raise ValueError(f"Invalid age: {data.age}. Must be between 0 and 120.")


def _inference_model_call(data: PassengerData) -> float:
    """
    Send a POST request to the ML inference service and parse the probability.
    """
    payload = data.model_dump()
    try:
        response = httpx.post(MODEL_API_URL, json=payload, timeout=5.0)
        response.raise_for_status()
        body = response.json()
    except httpx.RequestError as e:
        raise RuntimeError(f"Failed to connect to Model API: {e}")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Model API returned HTTP {e.response.status_code}: {e.response.text}")

    # Expect the response to contain a 'probability' key
    if 'probability' not in body:
        raise RuntimeError(f"Malformed response from Model API: {body}")

    try:
        return float(body['probability'])
    except (TypeError, ValueError):
        raise RuntimeError(f"Invalid probability value: {body['probability']}")


def _format_prediction_result(score: float) -> PredictionResult:
    """
    Convert raw score into a structured PredictionResult.
    """
    survived = score >= 0.5
    return PredictionResult(survived=survived, probability=score)
