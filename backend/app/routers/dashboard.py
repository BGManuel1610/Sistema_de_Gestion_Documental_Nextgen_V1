from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.radicado import Radicado
from ..models.usuario import Usuario
from ..schemas.dashboard import DashboardVencimientosResponse, RadicadoSemaforo
from ..security.jwt_handler import get_current_user
from ..security.access_control import exigir_roles

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/vencimientos", response_model=DashboardVencimientosResponse)
def dashboard_vencimientos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-010: Dashboard de Alertas y Vencimientos Legales.
    C.A.1: Calcula tiempo restante = rad_fecha_limite - NOW().
    C.A.2: < 24h y != 'FINALIZADO' -> grid_criticos con etiqueta 'CRÍTICO' (rojo).
    C.A.3: 24h - 72h -> etiqueta 'ATENCIÓN' (amarillo).
    C.A.4: > 72h -> etiqueta 'EN TIEMPO' (verde).
    """
    ahora = datetime.now()
    exigir_roles(current_user, "Administrador", "Gestionador")

    # Consultar radicados no finalizados (o todos si se desea comparar)
    query = db.query(Radicado).filter(Radicado.rad_estado != "FINALIZADO")
    if current_user.usr_rol != "Administrador":
        query = query.filter(
            Radicado.rad_sede_actual == current_user.usr_sede,
            Radicado.rad_usuario_gestionador == current_user.usr_id
        )
    radicados = query.all()

    grid_criticos: List[RadicadoSemaforo] = []
    grid_atencion: List[RadicadoSemaforo] = []
    grid_en_tiempo: List[RadicadoSemaforo] = []

    for r in radicados:
        delta = r.rad_fecha_limite - ahora
        horas_restantes = delta.total_seconds() / 3600.0

        if horas_restantes < 24.0:
            estado_semaforo = "CRÍTICO"
            item = RadicadoSemaforo(
                rad_id=r.rad_id,
                rad_codigo=r.rad_codigo,
                rad_remitente=r.rad_remitente,
                rad_asunto=r.rad_asunto,
                rad_sede_actual=r.rad_sede_actual,
                rad_estado=r.rad_estado,
                rad_fecha_creacion=r.rad_fecha_creacion,
                rad_fecha_limite=r.rad_fecha_limite,
                horas_restantes=round(horas_restantes, 1),
                estado_semaforo=estado_semaforo
            )
            grid_criticos.append(item)
        elif 24.0 <= horas_restantes <= 72.0:
            estado_semaforo = "ATENCIÓN"
            item = RadicadoSemaforo(
                rad_id=r.rad_id,
                rad_codigo=r.rad_codigo,
                rad_remitente=r.rad_remitente,
                rad_asunto=r.rad_asunto,
                rad_sede_actual=r.rad_sede_actual,
                rad_estado=r.rad_estado,
                rad_fecha_creacion=r.rad_fecha_creacion,
                rad_fecha_limite=r.rad_fecha_limite,
                horas_restantes=round(horas_restantes, 1),
                estado_semaforo=estado_semaforo
            )
            grid_atencion.append(item)
        else:
            estado_semaforo = "EN TIEMPO"
            item = RadicadoSemaforo(
                rad_id=r.rad_id,
                rad_codigo=r.rad_codigo,
                rad_remitente=r.rad_remitente,
                rad_asunto=r.rad_asunto,
                rad_sede_actual=r.rad_sede_actual,
                rad_estado=r.rad_estado,
                rad_fecha_creacion=r.rad_fecha_creacion,
                rad_fecha_limite=r.rad_fecha_limite,
                horas_restantes=round(horas_restantes, 1),
                estado_semaforo=estado_semaforo
            )
            grid_en_tiempo.append(item)

    # Ordenar críticos por menor tiempo restante (más urgente primero)
    grid_criticos.sort(key=lambda x: x.horas_restantes)
    grid_atencion.sort(key=lambda x: x.horas_restantes)
    grid_en_tiempo.sort(key=lambda x: x.horas_restantes)

    return DashboardVencimientosResponse(
        total_criticos=len(grid_criticos),
        total_atencion=len(grid_atencion),
        total_en_tiempo=len(grid_en_tiempo),
        grid_criticos=grid_criticos,
        grid_atencion=grid_atencion,
        grid_en_tiempo=grid_en_tiempo
    )
