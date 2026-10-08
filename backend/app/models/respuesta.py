from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database.base import Base

class Respuesta(Base):
    __tablename__ = "tbl_respuestas"

    res_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    res_rad_id = Column(Integer, ForeignKey("tbl_radicados.rad_id"), nullable=False, index=True)
    res_ruta_pdf = Column(String(500), nullable=False)
    res_observacion = Column(Text, nullable=False)
    res_fecha_cierre = Column(DateTime, server_default=func.now(), nullable=False)

    radicado = relationship("Radicado", back_populates="respuestas")
