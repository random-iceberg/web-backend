import uuid
from unittest.mock import AsyncMock, patch

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


async def test_train_model_success(client: TestClient, admin_user_token: str):
    """Test POST /models/train endpoint with valid data and admin role"""
    headers = {"Authorization": f"Bearer {admin_user_token}"}
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
        response = client.post("/models/train", json=payload, headers=headers)
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
    assert response.status_code == 403


async def test_train_model_invalid(client: TestClient, admin_user_token: str):
    """Test POST /models/train endpoint with invalid data and admin role"""
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    payload = {
        "algorithm": "Random Forest",
        "name": "Test Model",
        "features": [],  # Empty features should be rejected
    }
    response = client.post("/models/train", json=payload, headers=headers)
    assert response.status_code == 400


async def test_delete_model_success(client: TestClient, admin_user_token: str):
    """Test DELETE /models/{id} endpoint with admin role"""
    headers = {"Authorization": f"Bearer {admin_user_token}"}
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
        create_response = client.post("/models/train", json=payload, headers=headers)
    assert create_response.status_code == 200

    # Extract job_id and convert to model_id
    job_id = create_response.json()["job_id"]
    model_id = job_id.replace("train_", "")

    # Now delete the model
    delete_response = client.delete(f"/models/{model_id}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"


async def test_delete_model_forbidden_no_token(client: TestClient):
    """Test DELETE /models/{id} endpoint without token (anon role) - should be forbidden"""
    fake_id = str(uuid.uuid4())
    response = client.delete(f"/models/{fake_id}")
    assert response.status_code == 403


async def test_delete_nonexistent_model(client: TestClient, admin_user_token: str):
    """Test DELETE /models/{id} with non-existent ID and admin role"""
    headers = {"Authorization": f"Bearer {admin_user_token}"}
    fake_id = str(uuid.uuid4())
    response = client.delete(f"/models/{fake_id}", headers=headers)
    assert response.status_code == 404
