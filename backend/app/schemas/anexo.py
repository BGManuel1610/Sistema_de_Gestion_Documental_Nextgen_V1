from pydantic import BaseModel
from datetime import datetime

class AnexoResponse(BaseModel):
    anx_id: int
    anx_rad_id: int
    anx_nombre_original: str
    anx_ruta_archivo: str
    anx_tamano_kb: float
    anx_fecha_carga: datetime

    class Config:
        from_attributes = True
