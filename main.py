from fastapi import FastAPI
from routes import sermon
from dotenv import load_dotenv
from routes import auth
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*", "Authorization"],
)

app.include_router(sermon.router, prefix="/api/sermon", tags=["Sermon"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])


@app.get("/")
def root():
    return {
        "message": "Sermon Note AI is running",
    }
