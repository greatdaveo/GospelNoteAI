# Gospel Note AI API

This is the API for the Gospel Note AI mobile application. It is built with FastAPI and provides functionality for sermon transcription, summarization, Bible reference extraction, and storage. The API also manages user authentication, sermon retrieval, and synchronization between the mobile app and the server.

## Features

- User registration and authentication with JWT tokens
- Audio file upload and transcription
- Sermon summarization and automatic Bible reference extraction
- Save, update, and delete sermons in the database
- Retrieve sermons for the authenticated user
- Secure routes using token-based authentication
- PostgreSQL database with SQLAlchemy ORM

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT
- **Audio Transcription**: OpenAI Whisper
- **Summarization & Reference Extraction**: OpenAI GPT model
- **Storage**: PostgreSQL Database & Local storage
- **Environment Management**: Python-dotenv


## Setup and Installation

1. **Clone the repository**

```bash
git clone https://github.com/greatdaveo/SermonNote.git
cd server
```

2. **Create and activate virtual environment**
```bash   
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
Create a .env file in the server directory with:
DATABASE_URL=database_url
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
OPENAI_API_KEY=your_openai_key
```

5. **Run the server**
```bash
uvicorn main:app --reload
```

6. API Documentation
Once running, access:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## 👨‍💻 Developed By
> Olowomeye David [GitHub](https://github.com/greatdaveo) [LinkedIn](https://linkedin.com/in/greatdaveo)

---
