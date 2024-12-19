# Function til at validere et password
def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    if not any(char in "!@#$%^&*()-+" for char in password):
        return False
    return len(password) >= 8


# Function til at validere en email
def valide_email(email: str) -> bool:
    return "@" in email and "." in email


# Function til at validere et fornavn
def validate_first_name(first_name: str) -> bool:
    return len(first_name) >= 2


# Function til at validere et efternavn
def validate_last_name(last_name: str) -> bool:
    return len(last_name) >= 2


def validate_phone_number(phone_number: str) -> bool:
    if not phone_number.isdigit():
        return False
    return len(phone_number) == 8
