from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel
import sqlalchemy
from sqlalchemy.orm import Session

from app.models import UserModel
from app.core.db import get_session
from app.config import app_settings


# Конфигурация для JWT
SECRET_KEY = app_settings.secret_key  # Замените на реальный секретный ключ
ALGORITHM = app_settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = app_settings.access_token_expire_minutes

# Настройки для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема для OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def authenticate_user(email: str, password: str, session: Session):
    user = session.execute(sqlalchemy.select(UserModel).filter(UserModel.email == email)).scalars().first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = session.execute(sqlalchemy.select(UserModel).filter(UserModel.email == token_data.email)).scalars().first()
    if user is None:
        raise credentials_exception
    return user

# Пример эндпоинтов для FastAPI
from fastapi import APIRouter

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me/")
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    return current_user