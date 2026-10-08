import sys
import os

# Asegurar que reconozca el módulo app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.usuario import Usuario
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def crear_admin():
    db = SessionLocal()
    try:
        admin_existente = db.query(Usuario).filter(
            (Usuario.usr_email == "admin@docusol.com") | (Usuario.usr_email == "admin@nextgen.com")
        ).first()
        
        password_hash = pwd_context.hash("Password123!")
        
        if admin_existente:
            print("El usuario ya existe. Actualizando contraseña, email y estado...")
            admin_existente.usr_email = "admin@docusol.com"
            admin_existente.usr_password_hash = password_hash
            admin_existente.usr_estado = "ACTIVO"
            admin_existente.usr_rol = "Administrador"
            admin_existente.usr_sede = "Bogotá"
        else:
            print("Creando usuario administrador nuevo...")
            nuevo_admin = Usuario(
                usr_nombre="Carlos Admin",
                usr_email="admin@docusol.com",
                usr_password_hash=password_hash,
                usr_rol="Administrador",
                usr_sede="Bogotá",
                usr_estado="ACTIVO"
            )
            db.add(nuevo_admin)
            
        db.commit()
        print("¡Listo! Administrador configurado perfectamente.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    crear_admin()