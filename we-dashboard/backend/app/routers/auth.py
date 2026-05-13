from fastapi import APIRouter, HTTPException, status
from ..schemas import LoginRequest, TokenResponse
from ..security import create_access_token
from ..config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    if req.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    return TokenResponse(access_token=create_access_token("admin"))
