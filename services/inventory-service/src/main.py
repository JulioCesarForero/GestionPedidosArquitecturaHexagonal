from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "inventory-service"}

@app.get("/")
async def root():
    return {"message": "Inventory Service API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF