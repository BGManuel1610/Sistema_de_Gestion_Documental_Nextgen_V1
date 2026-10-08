from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ReporteFiltros(BaseModel):
    dtp_fecha_inicio: Optional[date] = None
    dtp_fecha_fin: Optional[date] = None
    cmb_filtro_sede: Optional[str] = "Todas"
    cmb_filtro_estado: Optional[str] = "Todos"

class ReporteItem(BaseModel):
    rad_id: int
    rad_codigo: str
    rad_remitente: str
    rad_asunto: str
    rad_tipo_doc: str
    rad_sede_destino: str
    rad_sede_actual: str
    rad_estado: str
    rad_fecha_creacion: datetime
    rad_fecha_limite: datetime

    class Config:
        from_attributes = True
