import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """使用 PBKDF2-SHA256 哈希密码（兼容性好，无需额外依赖）"""
    salt = secrets.token_hex(16)
    # 100000 次迭代
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"pbkdf2:sha256:100000:{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        parts = hashed_password.split(":")
        if len(parts) != 5:
            return False
        _, algorithm, iterations, salt, stored_key = parts
        iterations = int(iterations)
        key = hashlib.pbkdf2_hmac(
            algorithm, plain_password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        return secrets.compare_digest(key.hex(), stored_key)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
