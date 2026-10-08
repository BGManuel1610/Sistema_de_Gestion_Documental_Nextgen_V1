import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.usuario import Usuario
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def actualizar_usuarios():
    db = SessionLocal()
    try:
        usuarios = db.query(Usuario).all()
        nuevo_hash = pwd_context.hash("Password123!")
        
        print(f"Actualizando contraseñas para {len(usuarios)} usuarios...")
        for u in usuarios:
            u.usr_password_hash = nuevo_hash
            u.usr_estado = "ACTIVO"
            print(f" -> Actualizado: {u.usr_email} ({u.usr_rol})")
            
        db.commit()
        print("¡Listo! Todas las contraseñas fueron sincronizadas con éxito a 'Password123!'.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    actualizar_usuarios()