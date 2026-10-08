from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from datetime import datetime

class UsuarioCreate(BaseModel):
    txt_nombre: str
    txt_email: EmailStr
    cmb_rol: Literal["Administrador", "Radicador", "Gestionador"]
    cmb_sede: Literal["Bogotá", "Medellín", "Cali"]
    usr_password: Optional[str] = "Password123!"

class UsuarioRegistro(BaseModel):
    txt_nombre: str
    txt_email: EmailStr
    cmb_rol: Literal["Administrador", "Radicador", "Gestionador"]
    usr_password: str = "Password123!"
    admin_email: EmailStr
    admin_password: str

class UsuarioResponse(BaseModel):
    usr_id: int
    usr_nombre: str
    usr_email: str
    usr_rol: str
    usr_sede: str
    usr_estado: str
    usr_fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True
