from datetime import datetime, timedelta
import secrets, string


def generate_secret_key(length: int = 32) -> str:
    """Generate a secure secret key with uppercase letters."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))
