from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


# Patch responses for model service HTTP requests
def _mocked_model_list(*args, **kwargs):
    """Mocked response for model list GET request"""

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            # Return list of one model with a fake ID
            return [{"id": "mock-model-id"}]

    return Response()


def _mocked_predict(*args, **kwargs):
    """Mocked response for prediction POST request"""

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            # Return a plausible prediction payload
            return {"survived": True, "probability": 0.91}

    return Response()


async def _mocked_model_list_async(*args, **kwargs):
    return _mocked_model_list()


async def _mocked_predict_async(*args, **kwargs):
    return _mocked_predict()


# Test
async def test_predict_success(client: TestClient):
    """Test POST /predict endpoint with valid data"""
    payload = {
        "passengerClass": 3,
        "sex": "male",
        "age": 25,
        "fare": 7.25,  # Added required field
        "sibsp": 0,
        "parch": 0,
        "embarkationPort": "S",
        "title": "mr",  # Added required field
        "wereAlone": True,
        "cabinKnown": False,
    }
    with (
        patch(
            "httpx.AsyncClient.get", new=AsyncMock(side_effect=_mocked_model_list_async)
        ),
        patch(
            "httpx.AsyncClient.post", new=AsyncMock(side_effect=_mocked_predict_async)
        ),
    ):
        response = client.post(
            "/predict/", json=payload
        )  # Use /predict/ to avoid redirect
    assert response.status_code == 200, (
        f"Expected status code 200, got {response.status_code}"
    )

    data = response.json()
    # The response is now a MultiModelPredictionResult which is a dict
    assert isinstance(data, dict), "Response should be a dictionary"
    assert "mock-model-id" in data, "Response should contain the mock model ID"

    model_result = data["mock-model-id"]
    assert "survived" in model_result, "Model result missing 'survived' field"
    assert "probability" in model_result, "Model result missing 'probability' field"


async def test_get_prediction_history_empty(client: TestClient):
    """Test GET /predict/history endpoint when history is empty"""
    with (
        patch(
            "httpx.AsyncClient.get", new=AsyncMock(side_effect=_mocked_model_list_async)
        ),
        patch(
            "httpx.AsyncClient.post", new=AsyncMock(side_effect=_mocked_predict_async)
        ),
    ):
        response = client.get("/predict/history")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0  # Database is empty here


# TODO: add separate test: call /predict a few times, then check /predict/history
async def test_get_prediction_history(client: TestClient):
    """Test GET /predict/history endpoint with existing predictions"""
    # First, make a few predictions
    payload = {
        "passengerClass": 1,
        "sex": "female",
        "age": 38,
        "fare": 71.28,  # Added required field
        "sibsp": 1,
        "parch": 0,
        "embarkationPort": "C",
        "title": "mrs",  # Added required field
        "wereAlone": False,
        "cabinKnown": True,
    }
    with (
        patch(
            "httpx.AsyncClient.get", new=AsyncMock(side_effect=_mocked_model_list_async)
        ),
        patch(
            "httpx.AsyncClient.post", new=AsyncMock(side_effect=_mocked_predict_async)
        ),
    ):
        for _ in range(3):
            client.post("/predict/", json=payload)  # Use /predict/ to avoid redirect

        response = client.get("/predict/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        history_item = data[0]
        assert "timestamp" in history_item
        assert "input" in history_item
        assert "output" in history_item
