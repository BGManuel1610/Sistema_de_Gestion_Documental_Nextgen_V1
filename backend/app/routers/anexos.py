import os
import re
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.radicado import Radicado
from ..models.anexo import Anexo
from ..models.usuario import Usuario
from ..schemas.anexo import AnexoResponse
from ..security.jwt_handler import get_current_user, decode_access_token, security
from ..security.access_control import exigir_roles

router = APIRouter(prefix="/api/anexos", tags=["anexos"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR_ANEXOS", "uploads/anexos")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


def _sanear_nombre_archivo(filename: str) -> str:
    """Reduce el nombre del cliente a un token seguro para construir rutas en disco."""
    nombre = os.path.basename(filename or "").strip()
    nombre = re.sub(r"[^A-Za-z0-9._-]", "_", nombre)
    nombre = nombre.lstrip(".")
    return nombre or "documento.pdf"

def _obtener_usuario_archivo(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Usuario:
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token.strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado para acceder al archivo."
        )

    payload = decode_access_token(raw_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado."
        )

    usr_id = payload.get("sub")
    usuario = db.query(Usuario).filter(Usuario.usr_id == usr_id).first()
    if not usuario or usuario.usr_estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo."
        )

    return usuario

@router.get("/archivo/{anx_id}")
def obtener_archivo_anexo(
    anx_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_obtener_usuario_archivo)
):
    """
    Streaming y previsualización de un adjunto PDF específico por anx_id.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    anexo = db.query(Anexo).filter(Anexo.anx_id == anx_id).first()
    if not anexo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo adjunto no existe."
        )

    radicado = db.query(Radicado).filter(Radicado.rad_id == anexo.anx_rad_id).first()
    es_radicador_creador = radicado and radicado.rad_usuario_radicador == current_user.usr_id
    if not radicado or (
        current_user.usr_rol != "Administrador"
        and not es_radicador_creador
        and radicado.rad_sede_actual != current_user.usr_sede
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El radicado especificado no existe."
        )

    if not os.path.exists(anexo.anx_ruta_archivo):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo físico no fue encontrado en el servidor."
        )

    return FileResponse(
        path=anexo.anx_ruta_archivo,
        media_type="application/pdf",
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f'inline; filename="{anexo.anx_nombre_original}"'
        }
    )

# Alias de compatibilidad con la ruta documentada en el README (README:174).
@router.get("/download/{anexo_id}", include_in_schema=False)
def descargar_anexo_alias(
    anexo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_obtener_usuario_archivo)
):
    """README:174 declara GET /api/anexos/download/{anexo_id}; delega en la canonica."""
    return obtener_archivo_anexo(anexo_id, db, current_user)


# Alias de compatibilidad con la ruta documentada en el README (README:172).
# Se declara despues de /subir para no capturarla.
@router.post("/upload", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def subir_anexo_alias(
    rad_id: int = Form(...),
    file_adjunto: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """README:172 declara POST /api/anexos/upload; delega en la canonica /subir."""
    return await subir_anexo(rad_id, file_adjunto, db, current_user)


@router.get("/radicado/{rad_id}/archivo")
def obtener_archivo_por_radicado(
    rad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_obtener_usuario_archivo)
):
    """
    Streaming y previsualización del adjunto PDF más reciente de un radicado.
    """
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
            detail="El radicado especificado no existe."
        )

    anexo = (
        db.query(Anexo)
        .filter(Anexo.anx_rad_id == rad_id)
        .order_by(Anexo.anx_id.desc())
        .first()
    )
    if not anexo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El radicado no tiene archivos adjuntos."
        )

    if not os.path.exists(anexo.anx_ruta_archivo):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo físico no fue encontrado en el servidor."
        )

    return FileResponse(
        path=anexo.anx_ruta_archivo,
        media_type="application/pdf",
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f'inline; filename="{anexo.anx_nombre_original}"'
        }
    )

@router.get("/{rad_id}", response_model=List[AnexoResponse])
def listar_anexos_radicado(
    rad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista los anexos de un radicado para alimentar grid_anexos.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    radicado = db.query(Radicado).filter(Radicado.rad_id == rad_id).first()
    es_radicador_creador = radicado and radicado.rad_usuario_radicador == current_user.usr_id
    if not radicado or (
        current_user.usr_rol != "Administrador"
        and not es_radicador_creador
        and radicado.rad_sede_actual != current_user.usr_sede
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El radicado especificado no existe.")
    anexos = db.query(Anexo).filter(Anexo.anx_rad_id == rad_id).order_by(Anexo.anx_id.desc()).all()
    return anexos

@router.post("/subir", status_code=status.HTTP_201_CREATED)
async def subir_anexo(
    rad_id: int = Form(...),
    file_adjunto: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-004: Carga y Asociación de Adjuntos Digitales.
    C.A.2: Debe ser únicamente .pdf y <= 15MB.
    C.A.3: Bloqueo y mensaje exacto de error si no cumple.
    C.A.4: Guardar en servidor y en tbl_anexos.
    C.A.5: Retornar mensaje exacto y anexos actualizados.
    """
    exigir_roles(current_user, "Administrador", "Radicador", "Gestionador")
    # Verificar existencia del radicado
    radicado = db.query(Radicado).filter(Radicado.rad_id == rad_id).first()
    if not radicado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El radicado especificado no existe."
        )
    # Permitir al radicador adjuntar a radicados que él creó, aunque estén en otra sede
    es_radicador_creador = radicado.rad_usuario_radicador == current_user.usr_id
    if current_user.usr_rol != "Administrador" and not es_radicador_creador and radicado.rad_sede_actual != current_user.usr_sede:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El radicado especificado no existe.")

    # Validar que el radicado no esté finalizado
    if radicado.rad_estado == "FINALIZADO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden adjuntar documentos a un radicado finalizado."
        )

    # C.A.2 y C.A.3: Validar extensión .pdf
    filename = file_adjunto.filename or ""
    extension = os.path.splitext(filename)[1].lower()
    if extension != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato o tamaño de archivo no permitido. Solo se aceptan documentos PDF de hasta 15MB."
        )

    # Leer contenido para validar tamaño
    contents = await file_adjunto.read()
    tamano_bytes = len(contents)
    tamano_kb = round(tamano_bytes / 1024.0, 2)

    if tamano_bytes > MAX_FILE_SIZE_BYTES or tamano_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato o tamaño de archivo no permitido. Solo se aceptan documentos PDF de hasta 15MB."
        )

    # Guardar en servidor
    # El nombre viene del cliente, por lo que se sanea por completo: sin rutas
    # relativas ni separadores, para que un ".." no escape de UPLOAD_DIR.
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    nombre_sanitizado = _sanear_nombre_archivo(filename)
    safe_filename = f"{radicado.rad_codigo}_{timestamp_str}_{nombre_sanitizado}"
    destino_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Se confirma el realpath antes de escribir para garantizar que sigue dentro de UPLOAD_DIR.
    raiz = os.path.realpath(UPLOAD_DIR)
    if os.path.realpath(os.path.dirname(destino_path)) != raiz:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del archivo no es válido."
        )

    with open(destino_path, "wb") as f:
        f.write(contents)

    # C.A.4: Guardar en tbl_anexos
    nuevo_anexo = Anexo(
        anx_rad_id=rad_id,
        anx_nombre_original=filename,
        anx_ruta_archivo=destino_path.replace("\\", "/"),
        anx_tamano_kb=tamano_kb,
        anx_usuario_id=current_user.usr_id,
        anx_fecha_carga=datetime.now()
    )
    db.add(nuevo_anexo)
    db.commit()
    db.refresh(nuevo_anexo)

    # Consultar anexos actualizados para grid_anexos
    anexos_actualizados = db.query(Anexo).filter(Anexo.anx_rad_id == rad_id).order_by(Anexo.anx_id.desc()).all()

    # C.A.5: Mensaje exacto
    return {
        "mensaje": "Archivo adjuntado correctamente al radicado.",
        "anexo": AnexoResponse.model_validate(nuevo_anexo),
        "grid_anexos": [AnexoResponse.model_validate(a) for a in anexos_actualizados]
    }
