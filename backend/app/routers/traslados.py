from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from ..database.session import get_db
from ..models.radicado import Radicado
from ..models.historial_traslado import HistorialTraslado
from ..models.usuario import Usuario
from ..schemas.traslado import TrasladoCreate, TrasladoResponse
from ..schemas.radicado import RadicadoResponse
from ..security.jwt_handler import get_current_user
from ..security.access_control import exigir_misma_sede, exigir_roles
from ..utils.sedes import SEDES as SEDES_VALIDAS
from ..utils.audit import obtener_ip

router = APIRouter(prefix="/api/traslados", tags=["traslados"])


@router.get("/radicados-disponibles", response_model=List[RadicadoResponse], include_in_schema=False)
def listar_radicados_disponibles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    README:189 declara GET /api/traslados/radicados-disponibles.

    Aplica en el servidor las mismas reglas que usa POST /api/traslados, de modo
    que la UI no tenga que reconstruir el filtro en el cliente con criterios
    distintos (por ejemplo, ofrecer expedientes que despues serian rechazados).
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    query = db.query(Radicado).filter(Radicado.rad_estado.in_(["RADICADO", "ACEPTADO"]))
    if current_user.usr_rol != "Administrador":
        query = query.filter(Radicado.rad_sede_actual == current_user.usr_sede)
    return query.order_by(Radicado.rad_id.desc()).all()

@router.post("", status_code=status.HTTP_200_OK)
def trasladar_expediente(
    payload: TrasladoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-005: Reasignación y Traslado Inter-Sedes.
    C.A.1: Selección de radicado y nueva sede.
    C.A.2: Validación de motivo obligatorio.
    C.A.3: Actualizar rad_estado = 'TRASLADADO' y rad_sede_actual = cmb_nueva_sede.
    C.A.4: Insertar registro de auditoría en tbl_historial_traslados.
    C.A.5: Mensaje exacto de éxito.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    # C.A.2: Validar motivo obligatorio
    if not payload.txt_motivo_traslado or not payload.txt_motivo_traslado.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe ingresar el motivo o justificación del traslado inter-sede."
        )

    # Validar radicado
    radicado = db.query(Radicado).filter(Radicado.rad_id == payload.rad_id).first()
    if not radicado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El número de radicado ingresado no existe en el sistema."
        )
    if current_user.usr_rol != "Administrador":
        exigir_misma_sede(current_user, radicado.rad_sede_actual)
    if radicado.rad_estado == "FINALIZADO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El expediente ya se encuentra finalizado.")
    
    sede_origen = radicado.rad_sede_actual
    sede_destino = payload.cmb_nueva_sede.strip()

    if sede_destino not in SEDES_VALIDAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sede de destino seleccionada no es válida."
        )

    # Prohibicion de auto-traslado: mover a la misma sede no es un traslado inter-sede
    # y ensuciaria el historial de auditoria con un evento inexistente.
    if sede_destino == sede_origen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El expediente ya se encuentra en la sede seleccionada. No es posible trasladarlo a la misma sede."
        )

    # C.A.3: Actualizar tbl_radicados
    radicado.rad_estado = "TRASLADADO"
    radicado.rad_sede_actual = sede_destino
    radicado.rad_sede_destino = sede_destino
    # El expediente sale de la custodia del gestionador de la sede origen.
    radicado.rad_usuario_gestionador = None

    # C.A.4: Insertar en tbl_historial_traslados
    nuevo_traslado = HistorialTraslado(
        tra_rad_id=radicado.rad_id,
        tra_sede_origen=sede_origen,
        tra_sede_destino=sede_destino,
        tra_usuario_id=current_user.usr_id,
        tra_motivo=payload.txt_motivo_traslado.strip(),
        tra_ip_origen=obtener_ip(request),
        tra_fecha_hora=datetime.now()
    )
    db.add(nuevo_traslado)
    db.commit()
    db.refresh(nuevo_traslado)

    # C.A.5: Mensaje exacto
    return {
        "mensaje": "El expediente ha sido trasladado exitosamente a la sede seleccionada.",
        "traslado": TrasladoResponse.model_validate(nuevo_traslado)
    }
