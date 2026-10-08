import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database.session import get_db
from ..models.usuario import Usuario
from ..schemas.usuario import UsuarioCreate, UsuarioRegistro, UsuarioResponse
from ..security.hashing import get_password_hash, verify_password
from ..security.jwt_handler import get_current_user
from ..security.access_control import exigir_misma_sede, exigir_roles
from ..utils.sedes import sede_por_slug

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

#: Dominio corporativo obligatorio para toda cuenta creada desde la aplicacion.
DOMINIO_CORPORATIVO = os.getenv("DOMINIO_CORPORATIVO", "docusol.com")

@router.get("", response_model=List[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-002: Gestión de Cuentas de Usuario y Roles.
    C.A.1: Cargar tbl_lista_usuarios con información de nextgen_gd_db.tbl_usuarios.
    """
    exigir_roles(current_user, "Administrador")
    usuarios = db.query(Usuario).order_by(Usuario.usr_id.desc()).all()
    return usuarios

def _crear_usuario(db: Session, payload: UsuarioCreate, sede: str):
    email_clean = str(payload.txt_email).strip().lower()

    # README:147 exige obligatoriedad del correo corporativo @docusol.com.
    # Sin esta validacion un usuario externo podia autenticarse en la plataforma.
    if not email_clean.endswith("@" + DOMINIO_CORPORATIVO):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El correo debe pertenecer al dominio corporativo @{DOMINIO_CORPORATIVO}."
        )

    existe = db.query(Usuario).filter(Usuario.usr_email == email_clean).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo corporativo ya se encuentra registrado en la base de datos."
        )

    nuevo_usuario = Usuario(
        usr_nombre=payload.txt_nombre.strip(),
        usr_email=email_clean,
        usr_password_hash=get_password_hash(payload.usr_password or "Password123!"),
        usr_rol=payload.cmb_rol,
        usr_sede=sede,
        usr_estado="ACTIVO"
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return {
        "mensaje": "Usuario registrado exitosamente.",
        "usuario": UsuarioResponse.model_validate(nuevo_usuario)
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def crear_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-002: C.A.2, C.A.3, C.A.4, C.A.5.
    Valida correo único, inserta con usr_estado = 'ACTIVO' y devuelve mensaje exacto.
    """
    exigir_roles(current_user, "Administrador")
    return _crear_usuario(db, payload, payload.cmb_sede)

@router.post("/registro/{sede_slug}", status_code=status.HTTP_201_CREATED)
def registrar_usuario_desde_acceso(
    sede_slug: str,
    payload: UsuarioRegistro,
    db: Session = Depends(get_db)
):
    sede = sede_por_slug(sede_slug)
    if not sede:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La sede seleccionada no existe.")

    administrador = (
        db.query(Usuario)
        .filter(Usuario.usr_email == str(payload.admin_email).strip().lower())
        .first()
    )
    if (
        not administrador
        or administrador.usr_estado != "ACTIVO"
        or not verify_password(payload.admin_password, administrador.usr_password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de administrador no válidas."
        )
    exigir_roles(administrador, "Administrador")
    exigir_misma_sede(administrador, sede)

    crear_payload = UsuarioCreate(
        txt_nombre=payload.txt_nombre,
        txt_email=payload.txt_email,
        cmb_rol=payload.cmb_rol,
        cmb_sede=sede,
        usr_password=payload.usr_password
    )
    return _crear_usuario(db, crear_payload, sede)
