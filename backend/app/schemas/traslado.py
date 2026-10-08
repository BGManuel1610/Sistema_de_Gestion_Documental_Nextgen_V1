from pydantic import BaseModel
from datetime import datetime

class TrasladoCreate(BaseModel):
    rad_id: int
    cmb_nueva_sede: str
    txt_motivo_traslado: str

class TrasladoResponse(BaseModel):
    tra_id: int
    tra_rad_id: int
    tra_sede_origen: str
    tra_sede_destino: str
    tra_usuario_id: int
    tra_motivo: str
    tra_fecha_hora: datetime

    class Config:
        from_attributes = True
