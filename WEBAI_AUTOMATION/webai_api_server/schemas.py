from pydantic import BaseModel, Field
import datetime

class UserCreate(BaseModel):
    """
    Pydantic schema for user registration (`POST /auth/register`).

    Fields:
        username (str): The chosen username. Must be unique.
        password (str): The raw password (will be bcrypt-hashed before storage).
        email (Optional[str]): An optional email address for the user.
    """
    username: str
    password: str
    email: Optional[str] = None
class UserResponse(BaseModel):
    """
    Pydantic schema for returning user details.

    Returned by registration and auth endpoints. Excludes the hashed password,
    but includes the `api_key` which the user must send in the `X-API-Key`
    header for all subsequent authenticated requests.

    Fields:
        id (int): The unique identifier.
        username (str): The username.
        email (Optional[str]): The email address.
        created_at (datetime.datetime): When the account was registered.
    """
    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime.datetime
class LoginRequest(BaseModel):
    """
    Pydantic model for login request.

    Fields:
        username (str): The username of the user.
        password (str): The hashed password of the user.
    """
    username: str
    password: str
class Token(BaseModel):
    """
    Pydantic model for representing a token response.

    Fields:
        access_token (str): The access token.
        token_type (str): The type of the token.
    """
    access_token: str
    token_type: str
