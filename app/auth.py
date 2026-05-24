from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def _get_users() -> dict:
    settings = get_settings()
    users = {}
    for entry in settings.users.split(","):
        parts = entry.strip().split(":")
        if len(parts) == 2:
            users[parts[0]] = parts[1]
    return users

def verify_password(plain: str, stored: str) -> bool:
    try:
        return pwd_context.verify(plain, stored)
    except Exception:
        return plain == stored

def create_token(email: str) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({"sub": email, "exp": expire}, settings.jwt_secret, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return email
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")
