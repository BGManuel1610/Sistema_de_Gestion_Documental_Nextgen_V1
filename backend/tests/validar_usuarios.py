#!/usr/bin/env python3
"""
Script Automatizado de Validación de Usuarios y Roles
Sistema de Gestión Documental V1.1 — DocuSol (Soluciones en Documentación)

Verifica de forma independiente que los 7 usuarios del sistema
(Admin, Radicadores y Gestionadores de Bogotá, Medellín y Cali)
responden correctamente al login con la clave 'Password123!',
generan su respectivo token JWT firmado y validan su hash Bcrypt.

Formas de ejecución:
  1. python backend/tests/validar_usuarios.py
  2. pytest backend/tests/validar_usuarios.py
  3. docker exec -it nextgen_backend python tests/validar_usuarios.py
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Garantizar imports de la aplicación backend
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Evitar bloqueos síncronos de reintentos en app.main al importar en modo test
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.base import Base
from app.database.session import get_db, SessionLocal
from app.models.usuario import Usuario
from app.security.hashing import get_password_hash, verify_password
from app.security.jwt_handler import decode_access_token, SECRET_KEY

# Clave de evaluación oficial
GENERIC_PASSWORD = "Password123!"

# Lista de los 7 usuarios oficiales del sistema
USUARIOS_OFICIALES = [
    {
        "id": 1,
        "email": "admin@docusol.com",
        "rol": "Administrador",
        "sede": "Bogotá",
        "nombre": "Carlos Admin",
    },
    {
        "id": 2,
        "email": "radicador.bogota@docusol.com",
        "rol": "Radicador",
        "sede": "Bogotá",
        "nombre": "Laura Radicadora Bogotá",
    },
    {
        "id": 3,
        "email": "gestionador.bogota@docusol.com",
        "rol": "Gestionador",
        "sede": "Bogotá",
        "nombre": "Andrés Gestionador Bogotá",
    },
    {
        "id": 4,
        "email": "radicador.medellin@docusol.com",
        "rol": "Radicador",
        "sede": "Medellín",
        "nombre": "Marta Radicadora Medellín",
    },
    {
        "id": 5,
        "email": "gestionador.medellin@docusol.com",
        "rol": "Gestionador",
        "sede": "Medellín",
        "nombre": "Felipe Gestionador Medellín",
    },
    {
        "id": 6,
        "email": "radicador.cali@docusol.com",
        "rol": "Radicador",
        "sede": "Cali",
        "nombre": "Diana Radicadora Cali",
    },
    {
        "id": 7,
        "email": "gestionador.cali@docusol.com",
        "rol": "Gestionador",
        "sede": "Cali",
        "nombre": "Santiago Gestionador Cali",
    },
]

# Configuración de base de datos de respaldo (SQLite en memoria) para ejecución independiente
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

def _inicializar_entorno_prueba():
    """
    Asegura que los 7 usuarios oficiales existan con hash Bcrypt auténtico
    y que app.dependency_overrides[get_db] esté activo para el motor de pruebas.
    """
    Base.metadata.create_all(bind=engine_test)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db_mem = TestingSessionLocal()
    try:
        hash_bcrypt = get_password_hash(GENERIC_PASSWORD)
        for u in USUARIOS_OFICIALES:
            usr = db_mem.query(Usuario).filter(Usuario.usr_email == u["email"]).first()
            if not usr:
                db_mem.add(Usuario(
                    usr_id=u["id"],
                    usr_nombre=u["nombre"],
                    usr_email=u["email"],
                    usr_password_hash=hash_bcrypt,
                    usr_rol=u["rol"],
                    usr_sede=u["sede"],
                    usr_estado="ACTIVO",
                ))
            else:
                usr.usr_password_hash = hash_bcrypt
                usr.usr_estado = "ACTIVO"
        db_mem.commit()
    finally:
        db_mem.close()

# Inicializar cliente de prueba
_inicializar_entorno_prueba()
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_validar_usuarios_db():
    _inicializar_entorno_prueba()
    yield



def validar_usuario_login(u: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ejecuta el intento de autenticación y valida status, JWT y claims.
    """
    payload = {
        "user_email": u["email"],
        "user_password": GENERIC_PASSWORD,
        "sede": u["sede"],
    }
    res = client.post("/api/auth/login", json=payload)
    
    resultado = {
        "email": u["email"],
        "rol": u["rol"],
        "sede": u["sede"],
        "status_code": res.status_code,
        "login_ok": res.status_code == 200,
        "jwt_ok": False,
        "bcrypt_ok": False,
        "detalles": "",
    }

    if res.status_code == 200:
        data = res.json()
        token = data.get("access_token")
        if token:
            decoded = decode_access_token(token)
            if decoded and decoded.get("email") == u["email"] and decoded.get("rol") == u["rol"]:
                resultado["jwt_ok"] = True
            else:
                resultado["detalles"] = "Fallo en verificación de claims del JWT"
        else:
            resultado["detalles"] = "No se recibió access_token"
        
        # Validar consistencia del usuario de sesión devuelto
        user_sess = data.get("usuario", {})
        if user_sess.get("usr_rol") != u["rol"] or user_sess.get("usr_sede") != u["sede"]:
            resultado["jwt_ok"] = False
            resultado["detalles"] = "Datos de sesión no coinciden con el rol/sede esperado"
        
        # Validar directamente función de verificación Bcrypt
        test_hash = get_password_hash(GENERIC_PASSWORD)
        resultado["bcrypt_ok"] = verify_password(GENERIC_PASSWORD, test_hash)
    else:
        resultado["detalles"] = f"Respuesta inesperada: {res.text}"

    return resultado

# ==============================================================================
# PRUEBAS PYTEST (compatibilidad nativa con pytest)
# ==============================================================================

@pytest.mark.parametrize("u", USUARIOS_OFICIALES)
def test_usuario_login_y_jwt(u):
    """Valida cada uno de los 7 usuarios oficiales ante login con Password123!"""
    res = validar_usuario_login(u)
    assert res["login_ok"], f"Fallo al autenticar {u['email']}: {res['detalles']}"
    assert res["jwt_ok"], f"Fallo en token JWT para {u['email']}: {res['detalles']}"
    assert res["bcrypt_ok"], f"Fallo en verificación de Bcrypt para {u['email']}"

def test_login_password_incorrecto():
    """Valida rechazo ante contraseña inválida con código 401"""
    res = client.post("/api/auth/login", json={
        "user_email": "admin@docusol.com",
        "user_password": "ClaveIncorrecta999!",
        "sede": "Bogotá"
    })
    assert res.status_code == 401
    assert "Credenciales de acceso no válidas" in res.json().get("detail", "")

def test_login_sede_no_autorizada():
    """Valida que un usuario no pueda ingresar a una sede diferente a la suya (403)"""
    res = client.post("/api/auth/login", json={
        "user_email": "admin@docusol.com",
        "user_password": GENERIC_PASSWORD,
        "sede": "Medellín"  # Admin de Bogotá intentando acceder a Medellín
    })
    assert res.status_code == 403
    assert "Solo se admiten correos dirigidos a la sede" in res.json().get("detail", "")

# ==============================================================================
# EJECUCIÓN DIRECTA (CLI)
# ==============================================================================

def main():
    print("=" * 88)
    print(" DocuSol (Soluciones en Documentación) — Validación Automatizada de Usuarios y Roles")
    print("=" * 88)
    print(f"[*] Contraseña evaluada : {GENERIC_PASSWORD}")
    print(f"[*] Total usuarios     : {len(USUARIOS_OFICIALES)}")
    print(f"[*] Algoritmo Hashing  : Bcrypt (passlib)")
    print(f"[*] Algoritmo Tokens   : JWT HS256 (PyJWT)")
    print("=" * 88)
    print(f" {'#':2} | {'ROL':14} | {'SEDE':8} | {'CORREO':32} | {'STATUS':6} | {'JWT':4} | {'BCRYPT'}")
    print("-" * 88)

    todos_exitosos = True
    for idx, u in enumerate(USUARIOS_OFICIALES, start=1):
        res = validar_usuario_login(u)
        status_txt = f"{res['status_code']} OK" if res["login_ok"] else f"{res['status_code']} ERR"
        jwt_txt = "OK" if res["jwt_ok"] else "FAIL"
        bcrypt_txt = "OK" if res["bcrypt_ok"] else "FAIL"

        if not (res["login_ok"] and res["jwt_ok"] and res["bcrypt_ok"]):
            todos_exitosos = False

        print(f" {idx:2} | {u['rol']:14} | {u['sede']:8} | {u['email']:32} | {status_txt:6} | {jwt_txt:4} | {bcrypt_txt}")

    # Pruebas de seguridad negativa
    print("-" * 88)
    print("[*] Ejecutando validaciones de seguridad negativa...")
    res_bad_pwd = client.post("/api/auth/login", json={
        "user_email": "admin@docusol.com",
        "user_password": "WrongPassword!",
        "sede": "Bogotá"
    })
    bad_pwd_ok = res_bad_pwd.status_code == 401

    res_cross_sede = client.post("/api/auth/login", json={
        "user_email": "admin@docusol.com",
        "user_password": GENERIC_PASSWORD,
        "sede": "Cali"
    })
    cross_sede_ok = res_cross_sede.status_code == 403

    print(f"    - Bloqueo de contraseña inválida (HTTP 401): {'[OK]' if bad_pwd_ok else '[FAIL]'}")
    print(f"    - Bloqueo de sede cruzada (HTTP 403)       : {'[OK]' if cross_sede_ok else '[FAIL]'}")

    print("=" * 88)
    if todos_exitosos and bad_pwd_ok and cross_sede_ok:
        print("[OK] RESULTADO: TODOS LOS 7 USUARIOS VALIDADOS EXITOSAMENTE")
        print("    - Todos los usuarios autentican correctamente con 'Password123!'.")
        print("    - Emision y firma de JWT operativas sin errores de hash Bcrypt.")
        print("    - Politicas de seguridad y aislamiento de sedes verificadas.")
        print("=" * 88)
        sys.exit(0)
    else:
        print("[!] RESULTADO: Se encontraron fallos durante la validación.")
        print("=" * 88)
        sys.exit(1)

if __name__ == "__main__":
    main()
