from fastapi import FastAPI
from routes.sermon import router as SermonRouter
from dotenv import load_dotenv
from routes import auth

load_dotenv()

app = FastAPI()

app.include_router(SermonRouter, prefix="/api/sermon", tags=["Sermon"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
#

@app.get("/")
def root():
    return {
        "message": "Sermon Note AI is running",
    }
