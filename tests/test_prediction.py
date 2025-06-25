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
        "sibsp": 0,
        "parch": 0,
        "embarkationPort": "S",
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
        response = client.post("/predict", json=payload)
    assert response.status_code == 200, (
        f"Expected status code 200, got {response.status_code}"
    )

    data = response.json()
    assert "survived" in data, "Response missing 'survived' field"
    assert "probability" in data, "Response missing 'probability' field"


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
    assert len(data) == 0 

async def test_get_prediction_history(client: TestClient, user_id: str):
    """Test GET /predict/history endpoint with existing predictions"""
    # First, make a few predictions
    headers = {"user_id":user_id}

    payload = {
        "passengerClass": 1,
        "sex": "female",
        "age": 38,
        "sibsp": 1,
        "parch": 0,
        "embarkationPort": "C",
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
            client.post("/predict", json=payload, header=headers)

        response = client.get("/predict/history")
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
        "sibsp": 1,
        "parch": 0,
        "embarkationPort": "C",
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
            client.post("/predict", json=payload)

    # Check if response was successful and if response of history is empty. #
    response = client.get("/predict/history")
    assert response.status_code == 200
    assert response.json() == []

async def test_assert_different_user_history(client: TestClient, user_id_one: str, user_id_two: str):
    headers_one = {"user_id":user_id_one}
    headers_two = {"user_id":user_id_two}

    payload = {
        "passengerClass": 1,
        "sex": "female",
        "age": 38,
        "sibsp": 1,
        "parch": 0,
        "embarkationPort": "C",
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
            client.post("/predict", json=payload, headers=headers_one)
        for _ in range(2):
            client.post("/predict", json=payload, headers=headers_two)

    response_one = client.get("/predict/history", headers=headers_one)
    assert response_one.status_code == 200
    history_one = response_one.json()
    assert isinstance(history_one, list)
    assert len(history_one) == 3  # User one should have 3 predictions

    # 2. Test the history for the SECOND user
    response_two = client.get("/predict/history", headers=headers_two)
    assert response_two.status_code == 200
    history_two = response_two.json()
    assert isinstance(history_two, list)
    assert len(history_two) == 2
