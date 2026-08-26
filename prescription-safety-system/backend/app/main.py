from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Prescription Safety System",
    version="1.0.0"
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Prescription Safety System API"
    }