import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt
from app.core.config import settings

def get_password_hash(password: str) -> str:
    salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return f"{salt}${hashed}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if len(parts) != 2:
            return False
        salt, hashed = parts[0], parts[1]
        check = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        return check == hashed
    except Exception:
        return False

def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def encrypt_token(plain_token: str) -> str:
    """Encrypts integration token using SECRET_KEY."""
    if not plain_token or plain_token.startswith("enc_v1:"):
        return plain_token
    import base64
    key = (settings.SECRET_KEY * 4)[:32].encode('utf-8')
    token_bytes = plain_token.encode('utf-8')
    xor_bytes = bytes([b ^ key[i % len(key)] for i, b in enumerate(token_bytes)])
    return "enc_v1:" + base64.b64encode(xor_bytes).decode('utf-8')

def decrypt_token(encrypted_token: str) -> str:
    """Decrypts integration token using SECRET_KEY."""
    if not encrypted_token or not encrypted_token.startswith("enc_v1:"):
        return encrypted_token
    import base64
    try:
        raw_b64 = encrypted_token[7:]
        xor_bytes = base64.b64decode(raw_b64.encode('utf-8'))
        key = (settings.SECRET_KEY * 4)[:32].encode('utf-8')
        plain_bytes = bytes([b ^ key[i % len(key)] for i, b in enumerate(xor_bytes)])
        return plain_bytes.decode('utf-8')
    except Exception:
        return encrypted_token
