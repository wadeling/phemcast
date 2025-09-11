"""Authentication utilities for the Industry News Agent."""
# Suppress bcrypt warnings
import os
os.environ['PASSLIB_SUPPRESS_WARNINGS'] = '1'

# Fix bcrypt compatibility warning before importing passlib
try:
    import bcrypt
    if not hasattr(bcrypt, '__about__'):
        # Create a mock __about__ attribute to prevent passlib warnings
        class MockAbout:
            __version__ = getattr(bcrypt, '__version__', '4.0.0')
        bcrypt.__about__ = MockAbout()
except ImportError:
    pass

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select

from database import get_async_db
from db_models import User, InviteCode

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password."""
    async with await get_async_db() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


async def get_user_by_username(username: str) -> Optional[User]:
    """Get a user by username."""
    async with await get_async_db() as session:
        result = await session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()


async def get_user_by_email(email: str) -> Optional[User]:
    """Get a user by email."""
    async with await get_async_db() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def verify_invite_code(code: str) -> Optional[InviteCode]:
    """Verify if an invite code is valid and unused."""
    async with await get_async_db() as session:
        result = await session.execute(
            select(InviteCode).where(
                InviteCode.code == code,
                InviteCode.is_used == False
            )
        )
        invite_code = result.scalar_one_or_none()
        
        if invite_code and invite_code.expires_at:
            if datetime.utcnow() > invite_code.expires_at:
                return None
        
        return invite_code


async def use_invite_code(code: str, username: str):
    """Mark an invite code as used."""
    async with await get_async_db() as session:
        result = await session.execute(select(InviteCode).where(InviteCode.code == code))
        invite_code = result.scalar_one_or_none()
        
        if invite_code:
            invite_code.is_used = True
            invite_code.used_by = username
            invite_code.used_at = datetime.utcnow()
            await session.commit()


async def create_user(username: str, email: str, password: str, invite_code: str) -> User:
    """Create a new user."""
    async with await get_async_db() as session:
        # Check if username already exists
        existing_user = await get_user_by_username(username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )
        
        # Check if email already exists
        existing_email_user = await get_user_by_email(email)
        if existing_email_user:
            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )
        
        # Create user
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            invite_code_used=invite_code
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Mark invite code as used
        await use_invite_code(invite_code, username)
        
        return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get the current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
