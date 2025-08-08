from fastapi import FastAPI
from routes import sermon
from dotenv import load_dotenv
from routes import auth

load_dotenv()

app = FastAPI()

app.include_router(sermon.router, prefix="/api/sermon", tags=["Sermon"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])


@app.get("/")
def root():
    return {
        "message": "Sermon Note AI is running",
    }
