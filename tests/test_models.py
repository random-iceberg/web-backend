from fastapi.testclient import TestClient
from app.backend.main import app
import uuid

client = TestClient(app)

def test_list_models():
    """Test GET /models/ endpoint"""
    response = client.get("/models/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_train_model_success():
    """Test POST /models/train endpoint with valid data"""
    payload = {
        "algorithm": "Random Forest",
        "name": "Test Model",
        "features": ["pclass", "sex", "age", "fare"]
    }
    response = client.post("/models/train", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "training_started"

def test_train_model_invalid():
    """Test POST /models/train endpoint with invalid data"""
    payload = {
        "algorithm": "Random Forest",
        "name": "Test Model",
        "features": []  # Empty features should be rejected
    }
    response = client.post("/models/train", json=payload)
    assert response.status_code == 400

def test_delete_model():
    """Test DELETE /models/{id} endpoint"""
    # First create a model to delete
    payload = {
        "algorithm": "SVM",
        "name": "Delete Test Model",
        "features": ["pclass", "sex", "age"]
    }
    create_response = client.post("/models/train", json=payload)
    assert create_response.status_code == 200
    
    # Extract job_id and convert to model_id
    job_id = create_response.json()["job_id"]
    model_id = job_id.replace("train_", "")
    
    # Now delete the model
    delete_response = client.delete(f"/models/{model_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"

def test_delete_nonexistent_model():
    """Test DELETE /models/{id} with non-existent ID"""
    fake_id = str(uuid.uuid4())
    response = client.delete(f"/models/{fake_id}")
    assert response.status_code == 404