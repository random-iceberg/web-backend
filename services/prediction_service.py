from models.schemas import PassengerData, PredictionResult

def predict_survival(data: PassengerData) -> PredictionResult:
    """
    Simulates ML model inference for Titanic survival using heuristic logic.
    TODO: Replace this with your model integration call in production.
    """
    try:
        # Example heuristic: younger passengers or those paying high fare have improved chances.
        survived = data.age < 18 or data.fare > 50
        probability = 0.85 if survived else 0.15
        return PredictionResult(survived=survived, probability=probability)
    except Exception as exc:
        raise Exception(f"Error during prediction: {exc}")
