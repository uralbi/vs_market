import random
import string

def generate_password(length=12):
    """Generate a random password with uppercase, lowercase, digits, and special characters."""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
