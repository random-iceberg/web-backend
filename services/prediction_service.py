import os
import logging
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from db.schemas import Prediction
from models.schemas import PassengerData, PredictionResult

logger = logging.getLogger(__name__)


async def predict_survival(
    data: PassengerData, 
    db_session: AsyncSession, 
    model_id: Optional[str] = None
) -> PredictionResult:
    """
    Predict survival probability for a passenger.
    
    Args:
        data: Passenger information
        db_session: Database session for storing predictions
        model_id: Optional specific model to use (defaults to best available)
    
    Returns:
        PredictionResult with survival prediction and probability
    """
    MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model:8000")

    # Validate input data
    await _validate_passenger_data(data)

    # Select model to use
    if not model_id:
        model_id = await _select_best_model(MODEL_SERVICE_URL)
    
    # Perform inference
    result = await _inference_model_call(data, MODEL_SERVICE_URL, model_id)

    # Store prediction in database
    new_prediction = Prediction(
        input_data=data.model_dump(), 
        result=result.model_dump()
    )
    db_session.add(new_prediction)
    await db_session.commit()

    return result


async def _validate_passenger_data(data: PassengerData) -> None:
    """
    Validate passenger data beyond Pydantic validation.
    
    Raises:
        ValueError: If validation fails
    """
    # Class validation
    if data.passengerClass not in [1, 2, 3]:
        raise ValueError("Invalid passenger class: must be 1, 2 or 3.")

    # Sex validation
    if data.sex.lower() not in ["male", "female"]:
        raise ValueError("Invalid sex: must be 'male' or 'female'")

    # Age validation
    if not isinstance(data.age, (int, float)):
        raise ValueError("Invalid age: must be a number.")
    if data.age < 0 or data.age >= 120:
        raise ValueError("Invalid age: must be between 0 and 120.")

    # Family member validation
    if not isinstance(data.sibsp, int) or data.sibsp < 0:
        raise ValueError("Invalid sibsp: must be a non-negative integer.")
    if not isinstance(data.parch, int) or data.parch < 0:
        raise ValueError("Invalid parch: must be a non-negative integer.")

    # Embarkation port validation
    if data.embarkationPort.upper() not in ["C", "Q", "S"]:
        raise ValueError("Invalid embarkation port: must be 'C', 'Q', or 'S'.")

    # Boolean field validation
    if not isinstance(data.wereAlone, bool):
        raise ValueError("Invalid wereAlone: must be a boolean.")
    if not isinstance(data.cabinKnown, bool):
        raise ValueError("Invalid cabinKnown: must be a boolean.")


async def _select_best_model(model_service_url: str) -> str:
    """
    Select the best available model based on accuracy.
    Falls back to 'rf' (Random Forest) if no models are available.
    
    Args:
        model_service_url: URL of the model service
        
    Returns:
        Model ID to use for prediction
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{model_service_url}/models/",
                timeout=5.0
            )
            response.raise_for_status()
            models = response.json()
            
            if not models:
                logger.warning("No models available, using default 'rf'")
                return "rf"
            
            # Sort by accuracy and return the best one
            best_model = max(
                models, 
                key=lambda m: m.get("info", {}).get("accuracy", 0)
            )
            logger.info(
                f"Selected model {best_model['id']} with accuracy "
                f"{best_model.get('info', {}).get('accuracy', 0)}"
            )
            return best_model["id"]
            
    except Exception as e:
        logger.error(f"Error selecting model: {e}, falling back to 'rf'")
        return "rf"


async def _inference_model_call(
    data: PassengerData, 
    model_service_url: str, 
    model_id: str
) -> PredictionResult:
    """
    Call the model service for inference.
    
    Args:
        data: Passenger data
        model_service_url: URL of the model service
        model_id: ID of the model to use
        
    Returns:
        PredictionResult with survival prediction
        
    Raises:
        ValueError: If prediction fails
    """
    # Transform data to model service format
    input_data = _transform_passenger_data(data)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{model_service_url}/models/{model_id}/predict",
                json=input_data,
                timeout=10.0
            )
            response.raise_for_status()
            
            result = response.json()
            return PredictionResult(
                survived=result["survived"],
                probability=result["probability"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Model service returned error: {e.response.status_code} - "
                f"{e.response.text}"
            )
            raise ValueError(f"Prediction failed: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Error connecting to model service: {e}")
            raise ValueError("Unable to connect to prediction service")
        except Exception as e:
            logger.error(f"Unexpected error during prediction: {e}")
            raise ValueError("Unable to generate prediction")


def _transform_passenger_data(data: PassengerData) -> dict:
    """
    Transform passenger data from frontend format to model service format.
    
    Args:
        data: Passenger data in frontend format
        
    Returns:
        Dictionary in model service format
    """
    # Map embarkation ports
    embarked_map = {
        "C": "cherbourg",
        "Q": "queenstown", 
        "S": "southhampton"
    }
    
    # Infer title from sex and age
    title = _infer_title(data.sex, data.age, data.passengerClass)
    
    # Calculate fare based on class and embarkation port
    fare = _estimate_fare(data.passengerClass, data.embarkationPort)
    
    return {
        "pclass": data.passengerClass,
        "sex": data.sex,
        "age": data.age,
        "fare": fare,
        "travelled_alone": data.wereAlone,
        "embarked": embarked_map.get(data.embarkationPort, "southhampton"),
        "title": title,
    }


def _infer_title(sex: str, age: float, passenger_class: int) -> str:
    """
    Infer passenger title based on sex, age, and class.
    
    Args:
        sex: Passenger gender
        age: Passenger age
        passenger_class: Travel class (1, 2, or 3)
        
    Returns:
        Inferred title
    """
    if sex == "male":
        if age < 16:
            return "master"
        elif passenger_class == 1 and age > 40:
            # Wealthy older men might have rare titles
            return "rare"
        else:
            return "mr"
    else:  # female
        if age < 18:
            return "miss"
        elif passenger_class == 1 and age > 40:
            # Wealthy older women might have rare titles
            return "rare"
        else:
            # Simplified - in reality would need marital status
            return "mrs"


def _estimate_fare(passenger_class: int, embarkation_port: str) -> float:
    """
    Estimate fare based on passenger class and embarkation port.
    These are approximate historical averages from the Titanic dataset.
    
    Args:
        passenger_class: Travel class (1, 2, or 3)
        embarkation_port: Port of embarkation (C, Q, or S)
        
    Returns:
        Estimated fare

    TODO: Replace with actual fare estimation logic
    """
    # Base fares by class
    base_fare_by_class = {
        1: 84.15,   # First class average
        2: 20.66,   # Second class average
        3: 13.68    # Third class average
    }
    
    # Port adjustments (based on historical data)
    port_multiplier = {
        "C": 1.2,   # Cherbourg - typically higher fares
        "Q": 0.8,   # Queenstown - typically lower fares
        "S": 1.0    # Southampton - baseline
    }
    
    base_fare = base_fare_by_class.get(passenger_class, 20.0)
    multiplier = port_multiplier.get(embarkation_port, 1.0)
    
    return round(base_fare * multiplier, 2)
