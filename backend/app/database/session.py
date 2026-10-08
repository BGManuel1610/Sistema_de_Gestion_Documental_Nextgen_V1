import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Cargar automáticamente variables de entorno desde .env si existe en el entorno local
def _cargar_env_local():
    rutas_env = [
        Path(".env"),
        Path("../.env"),
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[3] / ".env"
    ]
    for p in rutas_env:
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("\"'")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass
            break

_cargar_env_local()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "NextGen2026*")
DB_HOST = os.getenv("DB_HOST", "nextgen_mysql")
DB_NAME = os.getenv("DB_NAME", "nextgen_gd_db")

# Determinación inteligente del puerto para aislamiento de XAMPP:
# - En Docker: DB_HOST es 'nextgen_mysql' y usa el puerto interno 3306 sobre la red bridge.
# - En Host local: si DB_HOST es 'localhost' o '127.0.0.1', usa el puerto externo 3307 (o inicio del rango 3307-3309)
#   evitando colisión con el servicio MySQL de XAMPP que suele ocupar el 3306.
raw_port = os.getenv("DB_PORT") or os.getenv("DB_PORT_EXTERNAL")
if not raw_port:
    raw_port = "3307" if DB_HOST in ("localhost", "127.0.0.1") else "3306"

# Si viene un rango (ej: "3307-3309"), extraer el puerto inicial numérico para el driver pymysql
if "-" in str(raw_port):
    DB_PORT = str(raw_port).split("-")[0].strip()
else:
    DB_PORT = str(raw_port).strip()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
