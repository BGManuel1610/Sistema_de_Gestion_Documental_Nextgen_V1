from pydantic import BaseModel
from datetime import datetime

class RespuestaResponse(BaseModel):
    res_id: int
    res_rad_id: int
    res_ruta_pdf: str
    res_observacion: str
    res_fecha_cierre: datetime

    class Config:
        from_attributes = True
