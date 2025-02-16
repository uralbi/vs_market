from app.domain.security.auth_token import decode_access_token


def get_current_user(token: str, user_service):
    payload = decode_access_token(token) # raises error if expired
    email = payload.get("sub")
    return user_service.get_user_by_email(email)