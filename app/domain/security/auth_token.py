import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
load_dotenv()


SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS'))

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Refresh token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid refresh token")
