import os
import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.radicado import Radicado
from ..models.respuesta import Respuesta
from ..models.historial_cierre import HistorialCierre
from ..models.usuario import Usuario
from ..schemas.respuesta import RespuestaResponse
from ..schemas.radicado import RadicadoResponse
from typing import List as _List

RadicadoResponseList = _List[RadicadoResponse]
from ..security.jwt_handler import get_current_user
from ..security.access_control import exigir_roles
from ..utils.audit import obtener_ip

router = APIRouter(prefix="/api/cierre", tags=["cierre"])

UPLOAD_DIR_RESPUESTAS = os.getenv("UPLOAD_DIR_RESPUESTAS", "uploads/respuestas")
os.makedirs(UPLOAD_DIR_RESPUESTAS, exist_ok=True)
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


def _sanear_nombre_archivo(filename: str) -> str:
    """Reduce el nombre del cliente a un token seguro para construir rutas en disco."""
    nombre = os.path.basename(filename or "").strip()
    nombre = re.sub(r"[^A-Za-z0-9._-]", "_", nombre)
    nombre = nombre.lstrip(".")
    return nombre or "respuesta.pdf"

@router.post("", status_code=status.HTTP_200_OK)
async def finalizar_tramite(
    rad_id: int = Form(...),
    txt_observacion_cierre: str = Form(""),
    file_respuesta: Optional[UploadFile] = File(None),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-007: Cierre y Finalización de Trámite Documental.
    C.A.1: Selección de PDF y observaciones.
    C.A.2: Si file_respuesta o txt_observacion_cierre están vacíos, mensaje exacto de error.
    C.A.3: Guardar en tbl_respuestas.
    C.A.4: Actualizar tbl_radicados.rad_estado = 'FINALIZADO'.
    C.A.5: Modo solo lectura y mensaje exacto de éxito.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    # C.A.2: Validar obligatoriedad de archivo PDF y observaciones
    if (file_respuesta is None or 
        not file_respuesta.filename or 
        not txt_observacion_cierre or 
        not txt_observacion_cierre.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Es obligatorio adjuntar el documento de respuesta en PDF y detallar las observaciones de cierre."
        )

    filename = file_respuesta.filename or ""
    extension = os.path.splitext(filename)[1].lower()
    if extension != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Es obligatorio adjuntar el documento de respuesta en PDF y detallar las observaciones de cierre."
        )

    # Validar existencia de radicado
    radicado = db.query(Radicado).filter(Radicado.rad_id == rad_id).first()
    if not radicado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El radicado especificado no existe."
        )
    # El Administrador actua como respaldo operativo y puede cerrar expedientes de
    # cualquier sede (HU-007). El resto de roles exige sede propia y radicado asignado.
    if current_user.usr_rol != "Administrador" and (
        radicado.rad_sede_actual != current_user.usr_sede
        or radicado.rad_usuario_gestionador != current_user.usr_id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El radicado especificado no existe.")

    # Si ya está finalizado, no permitir duplicar
    if radicado.rad_estado == "FINALIZADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El expediente ya se encuentra finalizado y en modo solo lectura."
        )

    # Guardar PDF de respuesta en servidor
    contents = await file_respuesta.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo PDF de respuesta está vacío."
        )
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato o tamaño de archivo no permitido. Solo se aceptan documentos PDF de hasta 15MB."
        )

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_filename = f"RESP_{radicado.rad_codigo}_{timestamp_str}_{_sanear_nombre_archivo(filename)}"
    destino_path = os.path.join(UPLOAD_DIR_RESPUESTAS, safe_filename)

    raiz = os.path.realpath(UPLOAD_DIR_RESPUESTAS)
    if os.path.realpath(os.path.dirname(destino_path)) != raiz:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre del archivo no es válido.")

    with open(destino_path, "wb") as f:
        f.write(contents)

    # C.A.3: Guardar en tbl_respuestas
    fecha_cierre = datetime.now()
    nueva_respuesta = Respuesta(
        res_rad_id=rad_id,
        res_ruta_pdf=destino_path.replace("\\", "/"),
        res_observacion=txt_observacion_cierre.strip(),
        res_fecha_cierre=fecha_cierre
    )
    db.add(nueva_respuesta)
    db.add(HistorialCierre(
        cierre_rad_id=rad_id,
        cierre_usuario_id=current_user.usr_id,
        # Se registra la sede del operador que ejecuto el cierre (incluido el
        # administrador en respaldo operativo).
        cierre_sede=current_user.usr_sede,
        cierre_ip_origen=obtener_ip(request),
        cierre_fecha_hora=fecha_cierre
    ))

    # C.A.4: Actualizar rad_estado = 'FINALIZADO'
    radicado.rad_estado = "FINALIZADO"

    db.commit()
    db.refresh(nueva_respuesta)
    db.refresh(radicado)

    # C.A.5: Notificación exacta
    return {
        "mensaje": "Trámite finalizado exitosamente. El expediente ha sido cerrado.",
        "respuesta": RespuestaResponse.model_validate(nueva_respuesta),
        "radicado": RadicadoResponse.model_validate(radicado)
    }

@router.get("/radicados-gestion", response_model=RadicadoResponseList, include_in_schema=False)
def listar_radicados_gestion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    README:218 declara GET /api/cierre/radicados-gestion: el listado de expedientes
    que el usuario actual puede cerrar. El frontend antes lo armaba filtrando
    /api/radicados en el cliente, con reglas distintas a las del backend.
    """
    exigir_roles(current_user, "Administrador", "Gestionador")
    query = db.query(Radicado).filter(Radicado.rad_estado != "FINALIZADO")
    if current_user.usr_rol == "Administrador":
        query = query.filter(Radicado.rad_sede_actual == current_user.usr_sede)
    else:
        query = query.filter(
            Radicado.rad_sede_actual == current_user.usr_sede,
            Radicado.rad_usuario_gestionador == current_user.usr_id,
        )
    return query.order_by(Radicado.rad_id.desc()).all()


@router.get("/{rad_id}")
def obtener_detalle_cierre(
    rad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene los datos del radicado y su respuesta (si existe) para la vista de solo lectura.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    radicado = db.query(Radicado).filter(Radicado.rad_id == rad_id).first()
    if not radicado or (current_user.usr_rol != "Administrador" and (
        radicado.rad_sede_actual != current_user.usr_sede
        or radicado.rad_usuario_gestionador != current_user.usr_id
    )):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El radicado especificado no existe."
        )
    respuesta = db.query(Respuesta).filter(Respuesta.res_rad_id == rad_id).first()
    
    return {
        "radicado": RadicadoResponse.model_validate(radicado),
        "respuesta": RespuestaResponse.model_validate(respuesta) if respuesta else None,
        "es_solo_lectura": radicado.rad_estado == "FINALIZADO"
    }
