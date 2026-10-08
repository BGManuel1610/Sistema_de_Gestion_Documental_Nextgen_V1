from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database.base import Base

class HistorialTraslado(Base):
    __tablename__ = "tbl_historial_traslados"

    tra_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tra_rad_id = Column(Integer, ForeignKey("tbl_radicados.rad_id"), nullable=False, index=True)
    tra_sede_origen = Column(String(50), nullable=False)
    tra_sede_destino = Column(String(50), nullable=False)
    tra_usuario_id = Column(Integer, ForeignKey("tbl_usuarios.usr_id"), nullable=False)
    tra_motivo = Column(Text, nullable=False)
    tra_fecha_hora = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    # Propuesta Comercial: la bitacora "especifica usuario, fecha, hora, sede y
    # direccion IP". NULL en los registros historicos anteriores.
    tra_ip_origen = Column(String(45), nullable=True)

    radicado = relationship("Radicado", back_populates="traslados")
    usuario_traslado = relationship("Usuario", back_populates="traslados_realizados")
