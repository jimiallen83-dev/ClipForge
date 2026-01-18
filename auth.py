from fastapi import APIRouter, Header, HTTPException, Depends, status
from typing import Optional
import db
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth")

SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    x_user_id: Optional[str] = Header(None), authorization: Optional[str] = Header(None)
):
    """Support demo header `X-User-Id` or Bearer JWT in `Authorization` header."""
    session = db.SessionLocal()
    try:
        # priority: Authorization Bearer token
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = int(payload.get("sub"))
            except JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            user = session.query(db.User).filter_by(id=user_id).first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return user

        if x_user_id:
            user = session.query(db.User).filter_by(id=int(x_user_id)).first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return user

        raise HTTPException(status_code=401, detail="Authentication required")
    finally:
        session.close()


@router.post("/register")
def register(email: str, password: str, name: Optional[str] = None):
    session = db.SessionLocal()
    try:
        existing = session.query(db.User).filter_by(email=email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        pwd_hash = get_password_hash(password)
        user = db.create_user(session, email, name=name, api_key=None)
        user.password_hash = pwd_hash
        session.add(user)
        session.commit()
        return {"user_id": user.id, "email": user.email}
    finally:
        session.close()


@router.post("/token")
def token(email: str, password: str):
    session = db.SessionLocal()
    try:
        user = session.query(db.User).filter_by(email=email).first()
        if (
            not user
            or not user.password_hash
            or not verify_password(password, user.password_hash)
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token({"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        session.close()


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "tier": user.tier}
