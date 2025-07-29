from fastapi import FastAPI
from routes.sermon import router as SermonRouter

app = FastAPI()

app.include_router(SermonRouter, prefix="/api/sermon", tags=["Sermon"])

@app.get("/")
def root():
    return {
        "message": "Sermon Note AI is running",
    }
