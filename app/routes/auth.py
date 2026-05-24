from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.auth import verify_password, create_token, _get_users

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    senha: str

class LoginResponse(BaseModel):
    token: str
    email: str

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    users = _get_users()
    stored = users.get(body.email)
    if not stored or not verify_password(body.senha, stored):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    token = create_token(body.email)
    return LoginResponse(token=token, email=body.email)
