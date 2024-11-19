# Function til at validere et password
def validate_password(password: str) -> bool:
    return len(password) >= 8


# Function til at validere en email
def valide_email(email: str) -> bool:
    return "@" in email and "." in email


# Function til at validere et brugernavn
def validate_username(username: str) -> bool:
    return len(username) >= 4


# Function til at validere et fornavn
def validate_first_name(first_name: str) -> bool:
    return len(first_name) >= 2


# Function til at validere et efternavn
def validate_last_name(last_name: str) -> bool:
    return len(last_name) >= 2
