from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database.session import get_db
from ..models.radicado import Radicado
from ..models.historial_traslado import HistorialTraslado
from ..models.usuario import Usuario
from ..schemas.radicado import RadicadoCreate, RadicadoResponse
from ..security.jwt_handler import get_current_user
from ..security.access_control import exigir_roles, exigir_misma_sede
from ..utils.consecutive import generate_radicado_code
from ..utils.business_days import sumar_dias_habiles_colombianos
from ..utils.sedes import SEDES
from ..utils.audit import obtener_ip

router = APIRouter(prefix="/api/radicados", tags=["radicados"])

@router.get("", response_model=List[RadicadoResponse])
def listar_radicados(
    estado: Optional[str] = None,
    sede: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista los radicados del sistema con filtros opcionales.
    """
    query = db.query(Radicado)
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    if current_user.usr_rol != "Administrador":
        query = query.filter(
            (Radicado.rad_sede_actual == current_user.usr_sede) |
            (Radicado.rad_usuario_radicador == current_user.usr_id)
        )
    if sede and sede != "Todas":
        if current_user.usr_rol != "Administrador":
            exigir_misma_sede(current_user, sede)
        query = query.filter(Radicado.rad_sede_actual == sede)
    if estado and estado != "Todos":
        query = query.filter(Radicado.rad_estado == estado)
    return query.order_by(Radicado.rad_id.desc()).all()

@router.get("/{rad_id}", response_model=RadicadoResponse)
def obtener_radicado(
    rad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    radicado = db.query(Radicado).filter(Radicado.rad_id == rad_id).first()
    es_radicador_creador = radicado and radicado.rad_usuario_radicador == current_user.usr_id
    if not radicado or (
        current_user.usr_rol != "Administrador"
        and not es_radicador_creador
        and radicado.rad_sede_actual != current_user.usr_sede
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El número de radicado ingresado no existe en el sistema."
        )
    return radicado

@router.post("", status_code=status.HTTP_201_CREATED)
def crear_radicado(
    payload: RadicadoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-003: Radicación de Documentos e Indización de Metadatos.
    C.A.2 & C.A.3: Validación de campos obligatorios.
    C.A.4: Inserción con código RAD-YYYY-XXXXX y rad_estado = 'RADICADO'.
    C.A.5: Mensaje exacto de éxito.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    # C.A.3: Validación de campos obligatorios
    if (not payload.txt_remitente.strip() or 
        not payload.txt_asunto.strip() or 
        not payload.cmb_tipo_doc.strip() or 
        not payload.cmb_sede_destino.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Por favor complete todos los campos obligatorios antes de continuar."
        )
    
    # Generar código RAD-YYYY-XXXXX
    codigo = generate_radicado_code(db)

    # Fecha límite (por defecto 5 días hábiles a partir de hoy).
    # El plazo corre desde la radicación, no desde la aceptación: la entidad
    #.reactive desde que recibe el documento y es lo que evita la caducidad
    # del término (Propuesta Comercial, "Mitigación Absoluta de Riesgo Legal").
    ahora = datetime.now()
    dias = payload.dias_termino if payload.dias_termino and 0 < payload.dias_termino <= 365 else 5
    fecha_limite = sumar_dias_habiles_colombianos(ahora, dias)

    sede_origen = current_user.usr_sede
    sede_destino = (payload.cmb_sede_destino or "").strip()
    if sede_destino not in SEDES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sede de destino seleccionada no es válida."
        )

    # Propuesta Comercial (Perfil Radicador): el radicador "asigna el documento
    # a una sede/destinatario" y realiza el "enrutamiento inicial hacia la sede
    # de destino". Si la sede destino es distinta a la del radicador, el
    # expediente queda en esa sede en estado TRASLADADO y espera la aceptación
    # formal de su gestionador (HU-006).
    es_derivacion = sede_destino != sede_origen

    nuevo_radicado = Radicado(
        rad_codigo=codigo,
        rad_remitente=payload.txt_remitente.strip(),
        rad_asunto=payload.txt_asunto.strip(),
        rad_tipo_doc=payload.cmb_tipo_doc.strip(),
        rad_sede_origen=sede_origen,
        rad_sede_destino=sede_destino,
        rad_sede_actual=sede_destino,
        rad_estado="TRASLADADO" if es_derivacion else "RADICADO",
        rad_usuario_radicador=current_user.usr_id,
        rad_fecha_creacion=ahora,
        rad_fecha_limite=fecha_limite
    )

    db.add(nuevo_radicado)
    db.flush()

    # La derivación inicial queda registrada en el historial para que la
    # trazabilidad (HU-008) muestre el movimiento desde el primer momento.
    if es_derivacion:
        db.add(HistorialTraslado(
            tra_rad_id=nuevo_radicado.rad_id,
            tra_sede_origen=sede_origen,
            tra_sede_destino=sede_destino,
            tra_usuario_id=current_user.usr_id,
            tra_motivo="Enrutamiento inicial en la radicación hacia la sede de destino",
            tra_ip_origen=obtener_ip(request),
        ))

    db.commit()
    db.refresh(nuevo_radicado)

    # C.A.5: Mensaje exacto con el código generado
    mensaje_exito = f"Radicado registrado con éxito bajo el código: {codigo}."

    return {
        "mensaje": mensaje_exito,
        "radicado": RadicadoResponse.model_validate(nuevo_radicado)
    }
