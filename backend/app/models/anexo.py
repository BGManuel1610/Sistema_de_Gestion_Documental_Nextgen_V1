from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database.base import Base

class Anexo(Base):
    __tablename__ = "tbl_anexos"

    anx_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    anx_rad_id = Column(Integer, ForeignKey("tbl_radicados.rad_id"), nullable=False, index=True)
    anx_nombre_original = Column(String(255), nullable=False)
    anx_ruta_archivo = Column(String(500), nullable=False)
    anx_tamano_kb = Column(Numeric(10, 2), nullable=False)
    anx_fecha_carga = Column(DateTime, server_default=func.now(), nullable=False)
    # Autor de la digitalizacion: la HU-008 exige el evento "Carga de anexos"
    # con usuario responsable en la linea de tiempo. NULL en filas preexistentes.
    anx_usuario_id = Column(Integer, ForeignKey("tbl_usuarios.usr_id"), nullable=True, index=True)

    radicado = relationship("Radicado", back_populates="anexos")
    usuario_carga = relationship("Usuario", foreign_keys=[anx_usuario_id])
