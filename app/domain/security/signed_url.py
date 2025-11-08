import time, hmac, hashlib, base64
import os
from fastapi import HTTPException
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY_URL") 
TOKEN_ENC_EXPIRY = 600  # 🔥 Key expires in 10 minutes
TOKEN_EXPIRY = 60
DOMAIN = os.getenv("DOMAIN")

def generate_signature(movie_id: str, filename: str) -> str:
    """
    Generates a secure HMAC-SHA256 signature for signed URLs.

    Args:
        movie_id (int): The movie ID.
        filename (str): The filename (e.g., "Python_720p.m3u8").

    Returns:
        str: A base64 URL-safe encoded signature.
    """
    expiry_time = int(time.time()) + 600                # Token expires in 10 minutes
    data = f"{movie_id}/{filename}/{expiry_time}"       # Concatenate data
    signature = hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return encoded_signature


def create_encryption_keyinfo():
    key_url = f"{DOMAIN}/api/movies/encryption_key"
    key_path = os.path.abspath("app/domain/security/encryption.key") 
    keyinfo_path = os.path.abspath("app/domain/security/encryption.keyinfo")
    if not os.path.exists(key_path):
        os.system(f"openssl rand 16 > {key_path}")
    iv_hex = os.urandom(16).hex()  
    with open(keyinfo_path, "w") as f:
        f.write(f"{key_url}\n{key_path}\n{iv_hex}\n") # Use a 16-byte IV
    print('Encryption key is generated')
        

def generate_signed_key_url(movie_id: str) -> str:
    """
    Generates a fresh signed URL for the encryption key.
    """
    expiry_time = int(time.time()) + TOKEN_ENC_EXPIRY
    data = f"encryption_key/{expiry_time}"

    signature = hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode()

    return f"{DOMAIN}/api/movies/encryption_key?exp={expiry_time}&sig={encoded_signature}"


def update_variant_playlists_with_signed_urls(hls_directory: str, movie_id: str):
    """
    Updates all variant .m3u8 playlists to contain signed URLs for .ts files.
    """
    for filename in os.listdir(hls_directory):
        if filename.endswith(".m3u8") and not filename.endswith("_master.m3u8"):
            variant_m3u8_path = os.path.join(hls_directory, filename)
            update_m3u8_with_signed_urls(variant_m3u8_path, movie_id)


def update_m3u8_with_signed_urls(m3u8_path: str, movie_id: str):
    """
    Reads the .m3u8 file, replaces .ts filenames with signed URLs.
    """
    with open(m3u8_path, "r") as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        idx = line.find(".ts")
        if ".ts" in line:
            segment_filename = line[:idx+3].strip()
            signed_url = generate_signed_url(movie_id, segment_filename)
            new_lines.append(signed_url + "\n")  # Replace with signed URL
        else:
            new_lines.append(line.strip() + "\n")
    
    with open(m3u8_path, "w") as file:
        file.writelines(new_lines)
        
        
def verify_signed_url(movie_id: str, segment_filename: str, exp: str, sig: str) -> bool:
    
    if int(exp) < int(time.time()):
        return False

    return True
    data = f"{movie_id}/{segment_filename}/{exp}"
    expected_signature = hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).digest()
    expected_encoded_signature = base64.urlsafe_b64encode(expected_signature).decode()

    return hmac.compare_digest(expected_encoded_signature, sig)


def verify_signed_enc_url(exp: str, sig: str) -> bool:
    """
    Verify if the signed URL for the encryption key is valid.

    Args:
        exp (str): Expiry timestamp from the URL.
        sig (str): HMAC signature from the URL.

    Returns:
        bool: True if the signature is valid and the link has not expired, False otherwise.
    """
    current_time = int(time.time())
    if int(exp) < current_time:
        print("Signature expired")
        return False
    data = f"encryption_key/{exp}"
    expected_signature = hmac.new(
        SECRET_KEY.encode(), data.encode(), hashlib.sha256
    ).digest()
    encoded_expected_signature = base64.urlsafe_b64encode(expected_signature).decode()
    if hmac.compare_digest(encoded_expected_signature, sig):
        return True
    else:
        print("Invalid signature")
        return False


def generate_signed_url(movie_id: str, segment_filename: str) -> str:
    expiry_time = int(time.time()) + TOKEN_EXPIRY
    encoded_signature = generate_signature(movie_id, segment_filename)
    return f"{segment_filename}?exp={expiry_time}&sig={encoded_signature}"


def generate_signed_m3u8(master_m3u8_path: str, movie_id: str) -> str:
    """
    Reads the master `.m3u8` file and generates a fresh version with signed URLs.
    Ensures it never returns None.
    """
    if not Path(master_m3u8_path).exists():
        raise HTTPException(status_code=404, detail="Master .m3u8 file not found")

    try:
        with open(master_m3u8_path, "r") as file:
            lines = file.readlines()
        
        updated_lines = []
        for line in lines:
            line = line.strip()

            # ✅ Replace only variant .m3u8 playlist links (not headers or comments)
            if line.endswith(".m3u8"):
                signed_url = generate_signed_url(movie_id, line)
                updated_lines.append(signed_url + "\n")
            else:
                updated_lines.append(line + "\n")

        updated_content = "".join(updated_lines)

        if not updated_content.strip():  # ✅ Ensure it's not empty
            raise HTTPException(status_code=500, detail="Generated .m3u8 content is empty")

        return updated_content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing .m3u8 file: {str(e)}")
