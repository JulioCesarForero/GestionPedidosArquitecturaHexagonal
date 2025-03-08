from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "payment-service"}

@app.get("/")
async def root():
    return {"message": "Payment Service API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)