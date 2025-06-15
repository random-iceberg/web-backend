from fastapi.testclient import TestClient


async def test_signup_does_not_fail(client: TestClient):
    payload = {
        "email": "someemail",
        "password": "somepass",
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 200


async def test_login_does_not_fail(client: TestClient):
    payload = {
        "email": "someemail",
        "password": "somepass",
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 200
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_token_is_usable(client: TestClient):
    payload = {
        "email": "someemail",
        "password": "somepass",
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 200
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    response = client.get("/auth/check", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    json = response.json()
    assert "sub" in json
    assert "exp" in json
