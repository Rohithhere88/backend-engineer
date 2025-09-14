
import os
import httpx
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Gateway",
    description="Simple API Gateway with load balancing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8031")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8032")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8033")

# Simple round-robin load balancer state
service_instances = {
    "user": [USER_SERVICE_URL],
    "product": [PRODUCT_SERVICE_URL],
    "order": [ORDER_SERVICE_URL]
}

current_index = {"user": 0, "product": 0, "order": 0}


def get_next_service(service_type: str) -> str:
    
    instances = service_instances[service_type]
    index = current_index[service_type]
    current_index[service_type] = (index + 1) % len(instances)
    return instances[index]


async def forward_request(
    service_type: str,
    path: str,
    method: str,
    headers: Dict[str, str],
    body: bytes = None,
    params: Dict[str, Any] = None
) -> JSONResponse:
    
    service_url = get_next_service(service_type)
    url = f"{service_url}{path}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Remove host header to avoid conflicts
            forward_headers = {k: v for k, v in headers.items() if k.lower() != "host"}
            
            response = await client.request(
                method=method,
                url=url,
                headers=forward_headers,
                content=body,
                params=params
            )
            
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    
    except httpx.TimeoutException:
        logger.error(f"Timeout forwarding request to {service_url}")
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        logger.error(f"Connection error forwarding request to {service_url}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.error(f"Error forwarding request to {service_url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "API Gateway is running", "services": list(service_instances.keys())}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "api-gateway"}



@app.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_service_proxy(request: Request, path: str):
    
    body = await request.body() if request.method in ["POST", "PUT"] else None
    params = dict(request.query_params)
    
    return await forward_request(
        "user",
        f"/users/{path}",
        request.method,
        dict(request.headers),
        body,
        params
    )


# Product Service Routes
@app.api_route("/products/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def product_service_proxy(request: Request, path: str):
    
    body = await request.body() if request.method in ["POST", "PUT"] else None
    params = dict(request.query_params)
    
    return await forward_request(
        "product",
        f"/products/{path}",
        request.method,
        dict(request.headers),
        body,
        params
    )


# Order Service Routes
@app.api_route("/orders/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def order_service_proxy(request: Request, path: str):
    
    body = await request.body() if request.method in ["POST", "PUT"] else None
    params = dict(request.query_params)
    
    return await forward_request(
        "order",
        f"/orders/{path}",
        request.method,
        dict(request.headers),
        body,
        params
    )


# Handle root level routes for each service
@app.api_route("/users", methods=["GET", "POST", "PUT", "DELETE"])
async def user_service_root_proxy(request: Request):
    
    body = await request.body() if request.method in ["POST", "PUT"] else None
    params = dict(request.query_params)
    
    return await forward_request(
        "user",
        "/users",
        request.method,
        dict(request.headers),
        body,
        params
    )


@app.api_route("/products", methods=["GET", "POST", "PUT", "DELETE"])
async def product_service_root_proxy(request: Request):
    
    body = await request.body() if request.method in ["POST", "PUT"] else None
    params = dict(request.query_params)
    
    return await forward_request(
        "product",
        "/products",
        request.method,
        dict(request.headers),
        body,
        params
    )


@app.api_route("/orders", methods=["GET", "POST", "PUT", "DELETE"])
async def order_service_root_proxy(request: Request):
    
    body = await request.body() if request.method in ["POST", "PUT"] else None
    params = dict(request.query_params)
    
    return await forward_request(
        "order",
        "/orders",
        request.method,
        dict(request.headers),
        body,
        params
    )
