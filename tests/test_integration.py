import pytest
import asyncio
import httpx

@pytest.mark.asyncio
class TestEcommerceIntegration:

    async def test_complete_order_flow_success(self, client: httpx.AsyncClient, wait_for_services):
        """Test complete order flow with successful inventory reservation"""
        # Register user
        user_data = {"email": "integration@example.com", "password": "password123", "name": "Integration User"}
        response = await client.post("http://localhost:8031/users/register", json=user_data)
        assert response.status_code == 200

        login_data = {"email": "integration@example.com", "password": "password123"}
        response = await client.post("http://localhost:8031/users/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create product
        product_data = {"name": "Integration Product", "description": "Test product", "price": 50.0, "quantity": 5}
        response = await client.post("http://localhost:8032/products", json=product_data, headers=headers)
        product_id = response.json()["id"]

        # Place order
        order_data = {"items": [{"product_id": product_id, "quantity": 2}], "idempotency_key": "integration-order-1"}
        response = await client.post("http://localhost:8033/orders", json=order_data, headers=headers)
        assert response.status_code == 200
        order_id = response.json()["id"]

        # Verify order
        await asyncio.sleep(2)
        response = await client.get(f"http://localhost:8033/orders/{order_id}", headers=headers)
        final_order = response.json()
        assert final_order["status"] == "confirmed"
        assert final_order["total_amount"] == 100.0

        # Verify product quantity
        response = await client.get(f"http://localhost:8032/products/{product_id}", headers=headers)
        assert response.json()["quantity"] == 3

    async def test_api_gateway_routing(self, client: httpx.AsyncClient, wait_for_services):
        """Check API Gateway routes correctly"""
        response = await client.get("http://localhost:8000/users/health")
        assert response.json()["service"] == "user-service"

        response = await client.get("http://localhost:8000/products/health")
        assert response.json()["service"] == "product-service"

        response = await client.get("http://localhost:8000/orders/health")
        assert response.json()["service"] == "order-service"

        response = await client.get("http://localhost:8000/health")
        assert response.json()["service"] == "api-gateway"
