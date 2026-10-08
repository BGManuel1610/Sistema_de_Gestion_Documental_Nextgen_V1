from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..database.session import get_db
from ..models.radicado import Radicado
from ..models.historial_aceptacion import HistorialAceptacion
from ..models.usuario import Usuario
from ..schemas.radicado import RadicadoResponse
from ..security.jwt_handler import get_current_user
from ..security.access_control import exigir_roles
from ..utils.audit import obtener_ip


class AceptarRequest(BaseModel):
    """Cuerpo de POST /api/recepcion/aceptar declarado en el README."""
    rad_id: int

router = APIRouter(prefix="/api/recepcion", tags=["recepcion"])

@router.get("/pendientes", response_model=List[RadicadoResponse])
def listar_pendientes_sede(
    sede: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-006: C.A.1
    En frm_bandeja_recepcion, grid_pendientes consulta tbl_radicados donde:
    rad_sede_actual = sede_usuario y rad_estado en ['RADICADO', 'TRASLADADO'].
    Si el usuario es Administrador, puede actuar como respaldo operativo de cualquier sede
    o consultar todas las sedes.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    query = (
        db.query(Radicado)
        .filter(Radicado.rad_estado.in_(["RADICADO", "TRASLADADO"]))
    )
    if current_user.usr_rol == "Administrador":
        if sede and sede not in ["Todas", "TODAS", "todas", "ALL"]:
            query = query.filter(Radicado.rad_sede_actual == sede)
        elif not sede and current_user.usr_sede:
            query = query.filter(Radicado.rad_sede_actual == current_user.usr_sede)
    else:
        query = query.filter(Radicado.rad_sede_actual == current_user.usr_sede)

    return query.order_by(Radicado.rad_id.desc()).all()

@router.get("/en_gestion", response_model=List[RadicadoResponse])
def listar_en_gestion(
    sede: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-006: C.A.4
    Expedientes aceptados en la bandeja de trabajo grid_en_gestion del usuario.
    Si el usuario es Administrador en respaldo operativo, puede ver los radicados
    asignados a él o los expedientes en gestión de la sede consultada.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    query = db.query(Radicado).filter(Radicado.rad_estado == "ACEPTADO")
    if current_user.usr_rol == "Administrador":
        if sede and sede not in ["Todas", "TODAS", "todas", "ALL"]:
            query = query.filter(Radicado.rad_sede_actual == sede)
        elif not sede and current_user.usr_sede:
            query = query.filter(
                (Radicado.rad_usuario_gestionador == current_user.usr_id) |
                (Radicado.rad_sede_actual == current_user.usr_sede)
            )
    else:
        query = query.filter(Radicado.rad_usuario_gestionador == current_user.usr_id)

    return query.order_by(Radicado.rad_id.desc()).all()

@router.post("/aceptar/{rad_id}", status_code=status.HTTP_200_OK)
def aceptar_radicado(
    rad_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-006: C.A.2, C.A.3, C.A.4, C.A.5
    Al hacer clic en btn_aceptar_radicado:
    - Actualizar rad_estado = 'ACEPTADO'
    - rad_usuario_gestionador = id_sesion
    - Mensaje exacto.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    radicado = db.query(Radicado).filter(Radicado.rad_id == rad_id).first()
    es_radicador_creador = radicado and radicado.rad_usuario_radicador == current_user.usr_id
    if not radicado or (current_user.usr_rol != "Administrador" and not es_radicador_creador and radicado.rad_sede_actual != current_user.usr_sede):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El radicado especificado no existe."
        )

    if radicado.rad_estado not in ["TRASLADADO", "RADICADO"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El expediente no está pendiente de recepción.")

    # C.A.3: Actualizar campos
    radicado.rad_estado = "ACEPTADO"
    radicado.rad_usuario_gestionador = current_user.usr_id
    db.add(HistorialAceptacion(
        acep_rad_id=radicado.rad_id,
        acep_usuario_id=current_user.usr_id,
        # Mismo criterio que el cierre: se registra la sede del operador que
        # ejecuta la accion, incluido el administrador en respaldo operativo.
        acep_sede=current_user.usr_sede or radicado.rad_sede_actual,
        acep_ip_origen=obtener_ip(request)
    ))

    db.commit()
    db.refresh(radicado)

    # C.A.5: Notificación emergente con el texto exacto
    return {
        "mensaje": "Expediente aceptado correctamente. Asignado a su bandeja de gestión.",
        "radicado": RadicadoResponse.model_validate(radicado)
    }


# Alias de compatibilidad con la ruta documentada en el README (README:204),
# que declara POST /api/recepcion/aceptar con el rad_id en el cuerpo.
@router.post("/aceptar", status_code=status.HTTP_200_OK, include_in_schema=False)
def aceptar_radicado_alias(
    payload: AceptarRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """README:204 declara POST /api/recepcion/aceptar; delega en la canonica."""
    return aceptar_radicado(payload.rad_id, request, db, current_user)
