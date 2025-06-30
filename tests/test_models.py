import uuid
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import status
from fastapi.testclient import TestClient


def _mocked_train_post(*args, **kwargs):
    """Mocked response for model training POST request"""

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            # Model service training returns info dict (simulate as needed)
            return {"info": {"accuracy": 0.95}}

    return Response()


async def _mocked_train_post_async(*args, **kwargs):
    return _mocked_train_post()


async def test_list_models(client: TestClient):
    """Test GET /models/ endpoint - accessible by all roles (anon)"""
    response = client.get("/models/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_train_model_success(admin_client: TestClient):
    """Test POST /models/train endpoint with valid data and admin role"""
    payload = {
        "algorithm": "Random Forest",
        "name": "Test Model",
        "features": ["pclass", "sex", "age", "fare"],
    }
    with (
        patch("httpx.AsyncClient.get", new=AsyncMock()),
        patch(
            "httpx.AsyncClient.post",
            new=AsyncMock(side_effect=_mocked_train_post_async),
        ),
    ):
        response = admin_client.post("/models/train", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "training_started"


async def test_train_model_forbidden_no_token(client: TestClient):
    """Test POST /models/train endpoint without token (anon role) - should be forbidden"""
    payload = {
        "algorithm": "Random Forest",
        "name": "Test Model",
        "features": ["pclass", "sex", "age", "fare"],
    }

    response = client.post("/models/train", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_train_model_forbidden_not_admin(user_client: TestClient):
    payload = {
        "algorithm": "Random Forest",
        "name": "Test Model",
        "features": ["pclass", "sex", "age", "fare"],
    }

    response = user_client.post("/models/train", json=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_train_model_invalid(admin_client: TestClient):
    """Test POST /models/train endpoint with invalid data and admin role"""
    payload = {
        "algorithm": "Random Forest",
        "name": "Test Model",
        "features": [],  # Empty features should be rejected
    }
    response = admin_client.post("/models/train", json=payload)
    assert response.status_code == 400


async def test_delete_model_success(admin_client: TestClient):
    """Test DELETE /models/{id} endpoint with admin role"""
    # First create a model to delete
    payload = {
        "algorithm": "SVM",
        "name": "Delete Test Model",
        "features": ["pclass", "sex", "age"],
    }
    with (
        patch("httpx.AsyncClient.get", new=AsyncMock()),
        patch(
            "httpx.AsyncClient.post",
            new=AsyncMock(side_effect=_mocked_train_post_async),
        ),
    ):
        create_response = admin_client.post("/models/train", json=payload)
    assert create_response.status_code == 200

    # Extract job_id and convert to model_id
    job_id = create_response.json()["job_id"]
    model_id = job_id.replace("train_", "")

    # Now delete the model
    delete_response = admin_client.delete(f"/models/{model_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"


async def test_delete_model_forbidden_no_token(client: TestClient):
    """Test DELETE /models/{id} endpoint without token (anon role) - should be forbidden"""
    fake_id = str(uuid.uuid4())
    response = client.delete(f"/models/{fake_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_delete_model_forbidden_not_admin(user_client: TestClient):
    """Test DELETE /models/{id} endpoint without token (anon role) - should be forbidden"""
    fake_id = str(uuid.uuid4())
    response = user_client.delete(f"/models/{fake_id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_delete_nonexistent_model(admin_client: TestClient):
    """Test DELETE /models/{id} with non-existent ID and admin role"""
    fake_id = str(uuid.uuid4())

    # Mock the model service GET request to return 404
    async def mock_get_404(*args, **kwargs):
        class Response:
            status_code = 404

            def raise_for_status(self):
                raise httpx.HTTPStatusError(
                    message="Not Found",
                    request=httpx.Request("GET", f"http://model:8000/models/{fake_id}"),
                    response=self,
                )

        return Response()

    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=mock_get_404)):
        response = admin_client.delete(f"/models/{fake_id}")
    assert response.status_code == 404
