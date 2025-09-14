"""
Test Configuration and Fixtures
"""
import pytest
import asyncio
import httpx
import pytest_asyncio

import time
from typing import AsyncGenerator


pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def wait_for_services():
    """Wait for all services to be healthy"""
    services = [
        "http://localhost:8000/health",  
        "http://localhost:8031/health",  
        "http://localhost:8032/health",  
        "http://localhost:8033/health",  
    ]
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient() as client:
                for service_url in services:
                    response = await client.get(service_url, timeout=5.0)
                    if response.status_code != 200:
                        raise Exception(f"Service {service_url} not healthy")
            print("All services are healthy!")
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_attempts}: {e}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(2)
            else:
                raise Exception("Services failed to become healthy")

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create HTTP client for testing"""
    async with httpx.AsyncClient() as c:
        yield c

@pytest_asyncio.fixture
async def auth_token(client: httpx.AsyncClient, wait_for_services) -> str:
    """Get authentication token for testing"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    response = await client.post("http://localhost:8031/users/register", json=user_data)
    assert response.status_code == 200

    login_data = {"email": "test@example.com", "password": "testpassword123"}
    response = await client.post("http://localhost:8031/users/login", json=login_data)
    assert response.status_code == 200
    token_data = response.json()
    return token_data["access_token"]

@pytest_asyncio.fixture
async def test_product_id(client: httpx.AsyncClient, auth_token: str) -> int:
    """Create a test product and return its ID"""
    product_data = {
        "name": "Test Product",
        "description": "A test product for testing",
        "price": 99.99,
        "quantity": 10
    }
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.post("http://localhost:8032/products", json=product_data, headers=headers)
    assert response.status_code == 200
    product = response.json()
    return product["id"]
