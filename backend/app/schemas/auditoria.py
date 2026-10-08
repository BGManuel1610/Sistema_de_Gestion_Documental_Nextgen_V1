from pydantic import BaseModel
from typing import Optional

class TrazabilidadItem(BaseModel):
    fecha_hora: str
    usuario: str
    sede_origen: str
    sede_destino: str
    accion_realizada: str
    estado: str
    # Propuesta Comercial: la bitacora registra usuario, fecha, hora, sede e IP.
    ip_origen: Optional[str] = None

class TrazabilidadResponse(BaseModel):
    rad_codigo: str
    rad_asunto: str
    rad_estado_actual: str
    linea_tiempo: list[TrazabilidadItem]
