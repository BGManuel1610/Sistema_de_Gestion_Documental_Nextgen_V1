from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RadicadoCreate(BaseModel):
    txt_remitente: str
    txt_asunto: str
    cmb_tipo_doc: str
    cmb_sede_destino: str
    dias_termino: Optional[int] = 5  # Días hábiles para rad_fecha_limite

class RadicadoResponse(BaseModel):
    rad_id: int
    rad_codigo: str
    rad_remitente: str
    rad_asunto: str
    rad_tipo_doc: str
    rad_sede_origen: Optional[str] = None
    rad_sede_destino: str
    rad_sede_actual: str
    rad_estado: str
    rad_usuario_radicador: int
    rad_usuario_gestionador: Optional[int] = None
    rad_fecha_creacion: datetime
    rad_fecha_limite: datetime

    class Config:
        from_attributes = True
