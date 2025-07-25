from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import requests

# 이 URL은 나중에 Gateway를 통해 접근 가능한 인증 서비스의 JWKS 엔드포인트가 됩니다.
# 지금은 임시 값으로 설정합니다.
JWKS_URL = "http://auth-service:8081/.well-known/jwks.json" 

algorithms = ["RS256"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token") # tokenUrl은 이제 사용되지 않지만 형식상 필요

class TokenData(BaseModel):
    sub: Optional[str] = None


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 여기서는 간단하게 토큰을 디코딩하지만,
        # 실제로는 JWKS에서 공개키를 가져와 서명을 검증해야 합니다.
        # 지금은 임시로 디코딩만 수행합니다.
        payload = jwt.decode(token, "your-secret-key", algorithms=algorithms, options={"verify_signature": False})
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(sub=username)
    except JWTError:
        raise credentials_exception
    # crud.get_user_by_email 대신, 토큰에서 추출한 사용자 ID(sub)를 그대로 사용합니다.
    # 실제로는 이 ID를 사용하여 DB에서 사용자 정보를 조회할 수 있습니다.
    user = {"id": token_data.sub, "email": token_data.sub} # 임시 사용자 객체
    return user