import base64
import hashlib
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from cryptography.fernet import Fernet
from .config import get_settings

settings = get_settings()


def _fernet_key() -> bytes:
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_fernet_key())


def encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")


def create_access_token(subject: str = "admin") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.JWT_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGO)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])
    except JWTError as e:
        raise ValueError(str(e))
