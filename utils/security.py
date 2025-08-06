from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sympy.utilities.decorator import deprecated
from datetime import datetime, timedelta
from jose import jwt
import os
import secrets


# Secret key to reset token
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
RESET_TOKEN_EXPIRY_SECONDS = 3600 # 1 hour

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 300
# Set up to hash password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def generate_access_token(email: str):
   serializer = URLSafeTimedSerializer(SECRET_KEY)
   return serializer.dumps(email)

def verify_reset_token(token: str) -> str:
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, max_age=RESET_TOKEN_EXPIRY_SECONDS)
        return email
    except (SignatureExpired, BadSignature):
        return "Error resetting password"

def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

