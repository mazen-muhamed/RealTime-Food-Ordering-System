from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import HTTPBearer
from jose import jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .database import get_db

from .schemas import (
    SignupRequest,
    LoginRequest,
)

from .repository import (
    get_user_by_email,
    get_user_by_phone,
    get_user_by_id,
    create_user,
)


router = APIRouter()


# =========================
# Password Hashing
# =========================

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    return password_hash.verify(
        plain_password,
        hashed_password,
    )


# =========================
# JWT Configuration
# =========================

SECRET_KEY = "change-this-secret-key"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# =========================
# OAuth2
# =========================

oauth2_scheme = HTTPBearer()



# =========================
# Decode JWT
# =========================

def decode_access_token(
    token: str,
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        return payload

    except Exception:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# =========================
# Get Current User
# =========================

def get_current_user(
    credentials=Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = get_user_by_id(
        db,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# =========================
# Signup
# =========================

@router.post(
    "/auth/signup",
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    payload: SignupRequest,
    db: Session = Depends(get_db),
):

    # Check email
    existing_user = get_user_by_email(
        db,
        payload.email,
    )

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check phone number
    existing_user = get_user_by_phone(
        db,
        payload.phone_number,
    )

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered",
        )

    # Hash password
    hashed_password = hash_password(
        payload.password,
    )

    # Create user
    user = create_user(
        db,
        username=payload.username,
        email=payload.email,
        phone_number=payload.phone_number,
        hashed_password=hashed_password,
    )

    return {
        "message": "Signup successful",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "phone_number": user["phone_number"],
        },
    }


# =========================
# Login
# =========================

@router.post("/auth/login")
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):

    # Find user
    user = get_user_by_email(
        db,
        payload.email,
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(
        payload.password,
        user["password"],
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create JWT
    access_token = create_access_token(
        data={
            "sub": str(user["id"])
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# =========================
# Current User
# =========================

@router.get("/auth/me")
async def get_me(
    current_user=Depends(get_current_user),
):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "phone_number": current_user["phone_number"],
    }

