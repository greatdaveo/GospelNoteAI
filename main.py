from fastapi import FastAPI
from routes.sermon import router as SermonRouter
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(SermonRouter, prefix="/api/sermon", tags=["Sermon"])

@app.get("/")
def root():
    return {
        "message": "Sermon Note AI is running",
    }
