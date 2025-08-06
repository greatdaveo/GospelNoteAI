import random

from fastapi import  APIRouter, HTTPException, Depends
from sqlmodel import  Session, select
from models.user import User
from schemas.user import UserCreate, UserRead, UserLogin, TokenResponse, UpdateProfile, ChangePassword, ForgotPasswordRequest, ResetPasswordOTPRequest, ResetPasswordRequest
from config.db import get_session
from utils.security import hash_password, verify_password, generate_reset_token, hash_password, create_access_token
from utils.token_store import reset_tokens
from utils.otp_store import set_otp, verify_otp
from utils.email import send_email
from datetime import datetime



router = APIRouter()

@router.post("/signup", response_model=UserRead)
def signup(user_data: UserCreate, session: Session = Depends(get_session)):
    # To check if the user exists
    existing_user = session.exec(select(User).where(User.email == user_data.email)).first()

    if existing_user:
        raise  HTTPException(
            status_code = 400,
            detail = "Email already registered"
        )

    hashed_pw = hash_password(user_data.password)
    user = User(
        name = user_data.name,
        email = user_data.email,
        password = hashed_pw
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_data.email)).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect password"
        )

    access_token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
         "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }

@router.put("/edit-profile", response_model=UserRead)
def update_profile(data: UpdateProfile, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email already in use"
        )

    user = session.exec(select(User)).first()
    if data.name:
        user.name = data.name
    if data.email:
        user.email = data.email

    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    return user

@router.put("/change-password", response_model=UserRead)
def change_password(data: ChangePassword, session: Session = Depends(get_session)):
    user = session.exec(select(User)).first()

    if not verify_password(data.current_password, user.password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect current password"
        )

    user.password = hash_password(data.new_password)
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    return user

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    otp = str(random.randint(100000, 999999))
    set_otp(data.email, otp)

    send_email(
        to = data.email,
        subject = "SERMON NOTE AI OTP Code",
        html=f"<h2>Reset Password</h2><p>Your OTP is: <b>{otp}</b>. It expires in 10 minutes.</p>"
    )

    # token = generate_reset_token()
    # reset_tokens[data.email] = token
    # print(f"Password reset link:  http://localhost:8000/reset-password?token={token}")

    return {
        "message": f"OTP has been sent to {data.email}",
    }

@router.post("/reset-password-otp")
def reset_password_otp(data: ResetPasswordOTPRequest, session: Session = Depends(get_session)):
    if not verify_otp(data.email, data.otp):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP"
        )

    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="User not found"
        )

    user.password = hash_password(data.new_password)
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()

    return {
        "message": "Password reset successful"
    }


# @router.post("/reset-password")
# def reset_password(data: ResetPasswordRequest, session: Session = Depends(get_session)):
#     for email, stored_token in reset_tokens.items():
#         if stored_token == data.token:
#             user = session.exec(select(User).where(User.email == email)).first()
#             if user:
#                 user.password = hash_password(data.new_password)
#                 user.updated_at = datetime.utcnow()
#
#                 session.add(user)
#                 session.commit()
#                 reset_tokens.pop(email)
#
#                 return {
#                     "message": "password reset successful"
#                 }
#
#     raise HTTPException(
#         status_code=400,
#         detail="Invalid or expired token"
#     )