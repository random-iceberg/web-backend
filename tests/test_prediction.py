from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, patch

from fastapi import status
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
    assert "mock-model-id" in data, f"Response missing model ID. Got: {data}"
    model_result = data["mock-model-id"]
    assert "survived" in model_result, "Model result missing 'survived' field"
    assert "probability" in model_result, "Model result missing 'probability' field"
    assert isinstance(model_result["survived"], bool)
    assert 0 <= model_result["probability"] <= 1


async def test_get_prediction_history(user_client: TestClient):
    """Test GET /predict/history endpoint with existing predictions"""

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
            _ = user_client.post("/predict", json=payload).raise_for_status()

        response = user_client.get("/predict/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


async def test_get_prediction_history_anonymous(client: TestClient):
    # Make prediction. #
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
            _ = client.post("/predict/", json=payload).raise_for_status()

    # Check if response was successful and if response of history is empty. #
    response = client.get("/predict/history")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_assert_different_user_history(
    client: TestClient, mk_user: Callable[[int], Awaitable[str]]
):
    user_id_one = await mk_user(1)
    user_id_two = await mk_user(2)

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
        client.cookies.set("access_token", user_id_one)
        for _ in range(3):
            _ = client.post("/predict", json=payload).raise_for_status()
        client.cookies.set("access_token", user_id_two)
        for _ in range(2):
            _ = client.post("/predict", json=payload).raise_for_status()

    client.cookies.set("access_token", user_id_one)
    response_one = client.get("/predict/history")
    assert response_one.status_code == 200
    history_one = response_one.json()
    assert isinstance(history_one, list)
    assert len(history_one) == 3  # User one should have 3 predictions

    # 2. Test the history for the SECOND user
    client.cookies.set("access_token", user_id_two)
    response_two = client.get("/predict/history")
    assert response_two.status_code == 200
    history_two = response_two.json()
    assert isinstance(history_two, list)
    assert len(history_two) == 2
