from fastapi import APIRouter, HTTPException
from python_jose import JWTError, jwt
from config import Config

router = APIRouter()

@router.post("/login")
def login(username: str, password: str):
    config = Config()
    if username == 'admin' and password == 'admin':
        token = config.generate_token('admin')
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/refresh")
def refresh_token(refresh_token: str):
    config = Config()
    try:
        payload = jwt.decode(refresh_token, config.JWT_SECRET, algorithms=['HS256'])
        token = config.generate_token(payload['sub'])
        return {"token": token}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/api_key")
def create_api_key(tenant_id: str):
    config = Config()
    api_key = config.generate_api_key(tenant_id)
    return {"api_key": api_key}