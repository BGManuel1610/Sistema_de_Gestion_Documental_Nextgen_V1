from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, func

from ..database.base import Base


class HistorialAceptacion(Base):
    __tablename__ = "tbl_historial_aceptaciones"

    acep_id = Column(Integer, primary_key=True, autoincrement=True)
    acep_rad_id = Column(Integer, ForeignKey("tbl_radicados.rad_id", ondelete="CASCADE"), nullable=False)
    acep_usuario_id = Column(Integer, ForeignKey("tbl_usuarios.usr_id"), nullable=False)
    acep_sede = Column(String(50), nullable=False)
    acep_fecha_hora = Column(DateTime, nullable=False, server_default=func.now())
    # Propuesta Comercial: la bitacora registra tambien la direccion IP.
    acep_ip_origen = Column(String(45), nullable=True)

    __table_args__ = (Index("idx_aceptaciones_rad_id", "acep_rad_id"),)