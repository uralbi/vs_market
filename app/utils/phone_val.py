import phonenumbers

def validate_phone(value: str) -> str | None:
    """Reused function for phone number validation and formatting."""
    if not value:
        return None
    try:
        value = value.strip()
        phone_number = phonenumbers.parse(value, "KG")
        pr = phonenumbers.format_number(phone_number, num_format=9)

        if len(str(phone_number.national_number)) < 6:
            raise ValueError("Invalid phone number")
        
        if phone_number.country_code != 996:
            pr = f"+{phone_number.country_code}-{pr}"
        elif len(str(phone_number.national_number)) < 7:
            pr = f"0-312-{pr}"
        else:
            pr = f"0-{pr}"
        return pr
    except Exception:
        raise ValueError("Invalid phone number")