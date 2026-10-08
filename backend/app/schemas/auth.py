from pydantic import BaseModel, EmailStr
from typing import Literal, Optional

class LoginRequest(BaseModel):
    user_email: str
    user_password: str
    sede: Optional[Literal["Bogotá", "Medellín", "Cali"]] = None

class UserSession(BaseModel):
    usr_id: int
    usr_nombre: str
    usr_email: str
    usr_rol: str
    usr_sede: str
    usr_estado: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UserSession
