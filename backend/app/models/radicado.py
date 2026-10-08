from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database.base import Base

class Radicado(Base):
    __tablename__ = "tbl_radicados"

    rad_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rad_codigo = Column(String(30), unique=True, nullable=False, index=True)
    rad_remitente = Column(String(150), nullable=False)
    rad_asunto = Column(Text, nullable=False)
    rad_tipo_doc = Column(String(50), nullable=False)
    rad_sede_origen = Column(String(50), nullable=True)
    rad_sede_destino = Column(String(50), nullable=False)
    rad_sede_actual = Column(String(50), nullable=False, index=True)
    rad_estado = Column(String(30), nullable=False, default="RADICADO", index=True)
    rad_usuario_radicador = Column(Integer, ForeignKey("tbl_usuarios.usr_id"), nullable=False)
    rad_usuario_gestionador = Column(Integer, ForeignKey("tbl_usuarios.usr_id"), nullable=True)
    rad_fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
    rad_fecha_limite = Column(DateTime, nullable=False, index=True)

    # Relaciones
    usuario_radicador = relationship("Usuario", foreign_keys=[rad_usuario_radicador], back_populates="radicados_creados")
    usuario_gestionador = relationship("Usuario", foreign_keys=[rad_usuario_gestionador], back_populates="radicados_gestionados")
    anexos = relationship("Anexo", back_populates="radicado", cascade="all, delete-orphan")
    traslados = relationship("HistorialTraslado", back_populates="radicado", cascade="all, delete-orphan")
    respuestas = relationship("Respuesta", back_populates="radicado", cascade="all, delete-orphan")
