import time, hmac, hashlib, base64
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY_URL") 
TOKEN_EXPIRY = 60

def verify_signed_url(movie_id: int, segment_filename: str, exp: str, sig: str) -> bool:
    if int(exp) < int(time.time()):
        return False

    data = f"{movie_id}/{segment_filename}/{exp}"
    expected_signature = hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).digest()
    expected_encoded_signature = base64.urlsafe_b64encode(expected_signature).decode()

    return hmac.compare_digest(expected_encoded_signature, sig)


def generate_signed_url(movie_id: int, segment_filename: str) -> str:
    expiry_time = int(time.time()) + TOKEN_EXPIRY
    data = f"{movie_id}/{segment_filename}/{expiry_time}"
    signature = hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).digest() # HMAC signature
    encoded_signature = base64.urlsafe_b64encode(signature).decode()

    return f"/api/movies/preview/{movie_id}/{segment_filename}?exp={expiry_time}&sig={encoded_signature}"
