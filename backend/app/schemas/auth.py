from pydantic import BaseModel


class LoginRequest(BaseModel):
    login_id: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    display_name: str
    login_id: str


class CurrentUser(BaseModel):
    role: str
    display_name: str
    login_id: str
