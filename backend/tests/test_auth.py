import pytest

@pytest.mark.asyncio
async def test_register_and_login(client):
    # 1. Register
    reg_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword"
    }
    response = await client.post("/api/auth/register", json=reg_data)
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "hashed_password" not in response.json()

    # 2. Login
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    token = response.json()["access_token"]

    # 3. Get Me
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

@pytest.mark.asyncio
async def test_login_wrong_password(client):
    # Register first
    reg_data = {
        "email": "wrong@example.com",
        "username": "wronguser",
        "password": "password123"
    }
    await client.post("/api/auth/register", json=reg_data)
    
    # Login with wrong password
    login_data = {
        "email": "wrong@example.com",
        "password": "wrongpassword"
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"
