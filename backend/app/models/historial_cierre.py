from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, func

from ..database.base import Base


class HistorialCierre(Base):
    __tablename__ = "tbl_historial_cierres"

    cierre_id = Column(Integer, primary_key=True, autoincrement=True)
    cierre_rad_id = Column(Integer, ForeignKey("tbl_radicados.rad_id", ondelete="CASCADE"), nullable=False)
    cierre_usuario_id = Column(Integer, ForeignKey("tbl_usuarios.usr_id"), nullable=False)
    cierre_sede = Column(String(50), nullable=False)
    cierre_fecha_hora = Column(DateTime, nullable=False, server_default=func.now())
    # Propuesta Comercial: la bitacora registra tambien la direccion IP.
    cierre_ip_origen = Column(String(45), nullable=True)

    __table_args__ = (
        Index("idx_cierres_rad_id", "cierre_rad_id", unique=True),
    )