import secrets
import os
from typing import List
from fastapi import FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

# Create a base for declarative models
Base = declarative_base()


# User model with verification fields
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)


# Pydantic models for input validation
class UserCreate(BaseModel):
    email: EmailStr


class EmailSchema(BaseModel):
    email: List[EmailStr]


# Get environment variables with defaults
mail_username = os.getenv("MAIL_USERNAME")
mail_password = os.getenv("MAIL_PASSWORD")
mail_from = os.getenv("MAIL_FROM")
mail_port = int(os.getenv("MAIL_PORT", "587"))  # Convert to int with default
mail_server = os.getenv("MAIL_SERVER")

# Print for debugging
print(f"Mail config: {mail_username}, {mail_server}, {mail_port}")

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=mail_username,
    MAIL_PASSWORD=mail_password,
    MAIL_FROM=mail_from,
    MAIL_PORT=mail_port,
    MAIL_SERVER=mail_server,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)
# Validate configuration
if not all([mail_username, mail_password, mail_from, mail_server]):
    raise ValueError(
        "Missing required email configuration. Check environment variables: "
        "MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM, MAIL_SERVER"
    )

app = FastAPI()


def generate_verification_token():
    """Generate a secure random verification token."""
    return secrets.token_urlsafe(32)


def create_verification_email_content(token: str, email: str):
    """Create HTML content for verification email."""
    verification_link = f"http://localhost:5173/verify?token={token}&email={email}"
    return f"""
    <html>
    <body>
        <h1>Velkomen Til Fitboks</h1>
        <h2>E-mail bekræftelse</h2>
        <p>Klik på linket nedenfor for at bekræfte din e-mail:</p>
        <a href="{verification_link}">Bekræfte e-mail</a>
        <p>Hvis du ikke har oprettet en konto, skal du ignorere denne e-mail.</p>
    </body>
    </html>
    
    """


async def send_verification_email(
    email: EmailStr, verification_token: str, fm: FastMail = FastMail(conf)
):
    """
    Send verification email to user

    Args:
        email: User's email address
        verification_token: Token for email verification
        fm: FastMail instance (optional)
    """
    message = MessageSchema(
        subject="Verify Your Email",
        recipients=[email],
        body=create_verification_email_content(verification_token, email),
        subtype=MessageType.html,
    )

    try:
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
