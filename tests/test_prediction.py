from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Test 
def test_predict_success():
    payload = {
        "pclass": 3,
        "sex": "male",
        "age": 25,
        "sibsp": 0,
        "parch": 0,
        "fare": 8.05,
        "embarked": "S",
    }
    response = client.post("/predict", json=payload)
    assert (
        response.status_code == 200
    ), f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert "survived" in data, "Response missing 'survived' field"
    assert "probability" in data, "Response missing 'probability' field"

async def test_get_prediction_history():
    response = await client.get("/predict/history")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    
    if len(data) > 0:
        history_item = data[0]
        assert "timestamp" in history_item
        assert "input" in history_item
        assert "output" in history_item
