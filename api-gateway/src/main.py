# api-gateway/src/main.py
import uvicorn
from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI()

# Configuración de URLs de servicios
services = {
    "orders": "http://order-service:8001",
    "inventory": "http://inventory-service:8002",
    "payments": "http://payment-service:8003"
}

@app.get("/")
async def root():
    return {
        "message": "API Gateway",
        "services": list(services.keys())
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.api_route("/{service}/{rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_endpoint(service: str, rest_of_path: str, request: Request):
    if service not in services:
        return {"detail": f"Service '{service}' not found"}
    
    # Construir la URL de destino
    target_url = f"{services[service]}/{rest_of_path}"
    print(f"Forwarding request to: {target_url}")
    
    # Obtener el método HTTP
    method = request.method
    
    # Obtener parámetros de consulta
    params = {}
    for k, v in request.query_params.items():
        params[k] = v
    
    # Obtener headers (excepto host)
    headers = {}
    for k, v in request.headers.items():
        if k.lower() != "host":
            headers[k] = v
    
    # Obtener body
    body = await request.body()
    
    # Realizar la solicitud
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=target_url,
                params=params,
                headers=headers,
                content=body
            )
        
        # Devolver la respuesta
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"detail": f"Error connecting to service: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)