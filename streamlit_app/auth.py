"""Authentication helpers — JWT + bcrypt, no FastAPI dependency."""
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from streamlit_app.services.config import get_secret


def _prepare(password: str) -> bytes:
    return hashlib.sha256(password.encode()).hexdigest().encode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(_prepare(plain), hashed.encode())


def create_access_token(user_id: str) -> str:
    secret = get_secret("JWT_SECRET_KEY", "changeme")
    algorithm = get_secret("JWT_ALGORITHM", "HS256")
    expire_minutes = int(get_secret("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str) -> Optional[str]:
    """Return user_id from token, or None if invalid/expired."""
    secret = get_secret("JWT_SECRET_KEY", "changeme")
    algorithm = get_secret("JWT_ALGORITHM", "HS256")
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload.get("sub")
    except JWTError:
        return None


def register_user(db, email: str, password: str, full_name: Optional[str] = None):
    """Create a new user. Returns (user, error_message)."""
    from streamlit_app.db.models import User
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return None, "Email sudah terdaftar"
    user = User(email=email, hashed_password=hash_password(password), full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, None


def login_user(db, email: str, password: str):
    """Verify credentials. Returns (token, error_message)."""
    from streamlit_app.db.models import User
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None, "Email atau password salah"
    token = create_access_token(str(user.id))
    return token, None
