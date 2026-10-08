from pydantic import BaseModel
from datetime import datetime
from typing import List

class RadicadoSemaforo(BaseModel):
    rad_id: int
    rad_codigo: str
    rad_remitente: str
    rad_asunto: str
    rad_sede_actual: str
    rad_estado: str
    rad_fecha_creacion: datetime
    rad_fecha_limite: datetime
    horas_restantes: float
    estado_semaforo: str  # 'CRÍTICO', 'ATENCIÓN', 'EN TIEMPO'

    class Config:
        from_attributes = True

class DashboardVencimientosResponse(BaseModel):
    total_criticos: int
    total_atencion: int
    total_en_tiempo: int
    grid_criticos: List[RadicadoSemaforo]
    grid_atencion: List[RadicadoSemaforo]
    grid_en_tiempo: List[RadicadoSemaforo]
