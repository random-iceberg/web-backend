from fastapi.testclient import TestClient

from .client import client as client
from .client import postgres_container as postgres_container


# Test
def test_predict_success(client: TestClient):
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
    response = client.post("/predict", json=payload)
    assert response.status_code == 200, (
        f"Expected status code 200, got {response.status_code}"
    )

    data = response.json()
    assert "survived" in data, "Response missing 'survived' field"
    assert "probability" in data, "Response missing 'probability' field"
