import time, hmac, hashlib, base64
import os
from fastapi import HTTPException
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY_URL") 
TOKEN_EXPIRY = 60


def update_variant_playlists_with_signed_urls(hls_directory: str, movie_id: int):
    """
    Updates all variant .m3u8 playlists to contain signed URLs for .ts files.
    """
    for filename in os.listdir(hls_directory):
        if filename.endswith(".m3u8") and not filename.endswith("_master.m3u8"):
            variant_m3u8_path = os.path.join(hls_directory, filename)
            update_m3u8_with_signed_urls(variant_m3u8_path, movie_id)


def update_m3u8_with_signed_urls(m3u8_path: str, movie_id: int):
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
    return f"{segment_filename}?exp={expiry_time}&sig={encoded_signature}"


def generate_signed_m3u8(master_m3u8_path: str, movie_id: int) -> str:
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
