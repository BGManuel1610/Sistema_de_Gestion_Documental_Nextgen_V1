from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.usuario import Usuario
from ..schemas.auth import LoginRequest, TokenResponse, UserSession
from ..security.hashing import verify_password
from ..security.jwt_handler import create_access_token, get_current_user

router = APIRouter(tags=["auth"])

def _autenticar_usuario(email: str, password: str, db: Session) -> Usuario:
    email_clean = (email or "").strip().lower()
    usuario = db.query(Usuario).filter(Usuario.usr_email == email_clean).first()
    
    # Validar existencia y hash Bcrypt
    if not usuario or not verify_password(password, usuario.usr_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso no válidas. Por favor verifique su correo y contraseña."
        )
    
    if usuario.usr_estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso no válidas. Por favor verifique su correo y contraseña."
        )
    
    return usuario

def _generar_token_respuesta(usuario: Usuario) -> TokenResponse:
    token = create_access_token(data={
        "sub": str(usuario.usr_id),
        "email": usuario.usr_email,
        "rol": usuario.usr_rol,
        "sede": usuario.usr_sede
    })
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        usuario=UserSession.model_validate(usuario)
    )

def _validar_sede_acceso(usuario: Usuario, sede: str = None) -> None:
    if sede and usuario.usr_sede != sede:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solo se admiten correos dirigidos a la sede {sede}."
        )

@router.post("/api/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    HU-001: Autenticación de Usuario y Control de Acceso (Login JSON).
    C.A.4: Valida credenciales contra nextgen_gd_db.tbl_usuarios.
    C.A.5: Mensaje exacto de error si no coinciden.
    """
    usuario = _autenticar_usuario(credentials.user_email, credentials.user_password, db)
    if credentials.sede:
        _validar_sede_acceso(usuario, credentials.sede)
    return _generar_token_respuesta(usuario)

@router.post("/token", response_model=TokenResponse)
@router.post("/api/auth/token", response_model=TokenResponse)
async def login_token(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint compatible con OAuth2 /token y pruebas automatizadas (acepta Form-data y JSON).
    Valida credenciales de cualquier rol y emite JWT firmado sin rechazo de hash.
    """
    email = None
    password = None
    sede = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("user_email") or body.get("username")
        password = body.get("user_password") or body.get("password")
        sede = body.get("sede")
    else:
        form_data = await request.form()
        email = form_data.get("user_email") or form_data.get("username")
        password = form_data.get("user_password") or form_data.get("password")
        sede = form_data.get("sede")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Por favor ingrese sus credenciales completas."
        )

    if sede and sede not in ("Bogotá", "Medellín", "Cali"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seleccione una sede válida."
        )

    usuario = _autenticar_usuario(str(email), str(password), db)
    if sede:
        _validar_sede_acceso(usuario, str(sede))
    return _generar_token_respuesta(usuario)

@router.get("/api/auth/me", response_model=UserSession)
def me(current_user: Usuario = Depends(get_current_user)):
    return UserSession.model_validate(current_user)
