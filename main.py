from fastapi import FastAPI
from routes import sermon
from dotenv import load_dotenv
from routes import auth
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "https://www.gospelnote.app",
    "https://gospelnote.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*", "Authorization", "Content-Type"],
)

app.include_router(sermon.router, prefix="/api/sermon", tags=["Sermon"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])


@app.get("/")
def root():
    return {
        "message": "Sermon Note AI is running",
    }

