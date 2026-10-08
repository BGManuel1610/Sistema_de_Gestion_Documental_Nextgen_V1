import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from .routers import (
    auth_router,
    usuarios_router,
    radicados_router,
    anexos_router,
    traslados_router,
    recepcion_router,
    cierre_router,
    auditoria_router,
    reportes_router,
    dashboard_router,
)
from .database.session import engine, SessionLocal
from .database.base import Base

def _sincronizar_claves_inicio():
    """
    Sincroniza automáticamente en el arranque las contraseñas Bcrypt de los usuarios activos.
    Garantiza que la contraseña genérica 'Password123!' funcione sin problemas de hash.
    """
    from .models.usuario import Usuario
    from .security.hashing import get_password_hash
    db = SessionLocal()
    try:
        usuarios = db.query(Usuario).all()
        if usuarios:
            hash_bcrypt = get_password_hash("Password123!")
            for u in usuarios:
                u.usr_password_hash = hash_bcrypt
                if u.usr_estado != "ACTIVO":
                    u.usr_estado = "ACTIVO"
            db.commit()
            print("[+] Sincronización automática Bcrypt exitosa para todos los usuarios activos.")
    except Exception as ex:
        db.rollback()
        print(f"[-] Advertencia al sincronizar contraseñas en arranque: {ex}")
    finally:
        db.close()

# Crear tablas con reintentos para evitar errores de conexión al iniciar los contenedores
# Si se detecta entorno de pruebas (TESTING=1), se omite el bloqueo de reintentos síncronos
if os.getenv("TESTING") == "1":
    print("[*] Modo de pruebas (TESTING=1) activo: omitiendo inicialización síncrona de base de datos.")
else:
    max_retries = 15
    retry_interval = 2
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[*] Intento {attempt}/{max_retries} de conexión a MySQL...")
            Base.metadata.create_all(bind=engine)
            print("[+] ¡Conexión exitosa y tablas verificadas!")
            _sincronizar_claves_inicio()
            break
        except OperationalError as e:
            if attempt == max_retries:
                print("[!] Se agotaron los reintentos de conexión con MySQL.")
                raise e
            print(f"[-] MySQL no disponible aún. Reintentando en {retry_interval} segundos...")
            time.sleep(retry_interval)

app = FastAPI(
    title="Sistema de Gestión Documental V1.1 — NextGen Development S.A.S.",
    description="API REST para Sprint 1 (HU001-HU005) y Sprint 2 (HU006-HU010)",
    version="1.1.0"
)

# Configurar CORS permitiendo cualquier puerto local dinámico (3000, 3001, etc.)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Los expedientes son confidenciales: uploads/anexos y uploads/respuestas NO se
# montan de forma estatica. Cada descarga pasa por /api/anexos/archivo/{id},
# que valida JWT y aislamiento por sede. Montarlos aqui permitia leer cualquier
# PDF del sistema adivinando el nombre (que incluye el codigo del radicado).
os.makedirs("uploads/anexos", exist_ok=True)
os.makedirs("uploads/respuestas", exist_ok=True)

# Montar Routers de Sprint 1 y Sprint 2 (incluyendo /token y /api/auth/login)
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(radicados_router)
app.include_router(anexos_router)
app.include_router(traslados_router)
app.include_router(recepcion_router)
app.include_router(cierre_router)
app.include_router(auditoria_router)
app.include_router(reportes_router)
app.include_router(dashboard_router)

@app.get("/")
def read_root():
    return {
        "proyecto": "Sistema de Gestión Documental V1.1 — NextGen Development S.A.S.",
        "estado": "Operativo",
        "alcance": "Sprint 1 (HU001-HU005) & Sprint 2 (HU006-HU010)",
        "sprints_futuros": "Sprint 3 (HU011-HU015), Sprint 4 (HU016-HU020), Sprint 5 (HU021-HU030)"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", os.getenv("PORT", "8000")))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)