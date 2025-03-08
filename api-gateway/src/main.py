# api-gateway/src/main.py
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
import httpx
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Environment variables for service URLs
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")

# Create FastAPI app
app = FastAPI(title="Microservices API Gateway", version="1.0.0")

# HTTP client for making requests to services
http_client = httpx.AsyncClient(timeout=30.0)

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

# Routes mapping
SERVICE_ROUTES = {
    "orders": f"{ORDER_SERVICE_URL}/api",
    "inventory": f"{INVENTORY_SERVICE_URL}/api",
    "payments": f"{PAYMENT_SERVICE_URL}/api"
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "services": {
        "order_service": ORDER_SERVICE_URL,
        "inventory_service": INVENTORY_SERVICE_URL,
        "payment_service": PAYMENT_SERVICE_URL
    }}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(service: str, path: str, request: Request):
    """
    Generic route that proxies requests to the appropriate microservice
    """
    if service not in SERVICE_ROUTES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
    
    # Get the target URL
    target_url = f"{SERVICE_ROUTES[service]}/{path}"
    logger.info(f"Proxying request to {target_url}")
    
    # Get the request body
    body = await request.body()
    
    # Get the request headers
    headers = dict(request.headers)
    # Remove headers that should not be forwarded
    headers.pop("host", None)
    
    # Forward the request to the target service
    try:
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params,
        )
        
        # Return the response from the microservice
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except httpx.RequestError as e:
        logger.error(f"Error proxying request to {target_url}: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"detail": f"Service '{service}' is unavailable"}
        )

# User-friendly routes for the front-end
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Microservices API Gateway",
        "available_services": list(SERVICE_ROUTES.keys()),
        "documentation": "/docs"
    }

