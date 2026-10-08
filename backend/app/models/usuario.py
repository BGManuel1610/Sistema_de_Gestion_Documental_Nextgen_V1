from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from ..database.base import Base

class Usuario(Base):
    __tablename__ = "tbl_usuarios"

    usr_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usr_nombre = Column(String(100), nullable=False)
    usr_email = Column(String(120), unique=True, nullable=False, index=True)
    usr_password_hash = Column(String(255), nullable=False)
    usr_rol = Column(String(50), nullable=False, index=True)
    usr_sede = Column(String(50), nullable=False, index=True)
    usr_estado = Column(String(20), nullable=False, default="ACTIVO")
    usr_fecha_creacion = Column(DateTime, server_default=func.now())

    # Relaciones para Sprint 1 y 2
    radicados_creados = relationship("Radicado", foreign_keys="Radicado.rad_usuario_radicador", back_populates="usuario_radicador")
    radicados_gestionados = relationship("Radicado", foreign_keys="Radicado.rad_usuario_gestionador", back_populates="usuario_gestionador")
    traslados_realizados = relationship("HistorialTraslado", back_populates="usuario_traslado")
    anexos_cargados = relationship("Anexo", back_populates="usuario_carga")
