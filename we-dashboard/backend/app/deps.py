from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


async def require_auth(token: str = Depends(oauth2_scheme)) -> str:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload.get("sub", "admin")
