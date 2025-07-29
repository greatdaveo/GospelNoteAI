from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Sermon Note AI is running",
    }
