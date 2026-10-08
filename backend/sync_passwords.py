#!/usr/bin/env python3
"""
Script de sincronización y actualización de contraseñas con Bcrypt para DocuSol — Soluciones en Documentación.
Ejecución en el contenedor:
    docker exec -it nextgen_backend python sync_passwords.py
"""

import os
import sys
import time

# Asegurar importación de los módulos de la app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal, engine
from app.models.usuario import Usuario
from app.security.hashing import get_password_hash, verify_password

GENERIC_PASSWORD = "Password123!"

# Lista de usuarios oficiales de evaluación (Admin, Radicadores y Gestionadores para Bogotá, Medellín y Cali)
USUARIOS_OFICIALES = [
    {
        "usr_id": 1,
        "usr_nombre": "Carlos Admin",
        "usr_email": "admin@docusol.com",
        "usr_rol": "Administrador",
        "usr_sede": "Bogotá",
        "usr_estado": "ACTIVO",
    },
    {
        "usr_id": 2,
        "usr_nombre": "Laura Radicadora Bogotá",
        "usr_email": "radicador.bogota@docusol.com",
        "usr_rol": "Radicador",
        "usr_sede": "Bogotá",
        "usr_estado": "ACTIVO",
    },
    {
        "usr_id": 3,
        "usr_nombre": "Andrés Gestionador Bogotá",
        "usr_email": "gestionador.bogota@docusol.com",
        "usr_rol": "Gestionador",
        "usr_sede": "Bogotá",
        "usr_estado": "ACTIVO",
    },
    {
        "usr_id": 4,
        "usr_nombre": "Marta Radicadora Medellín",
        "usr_email": "radicador.medellin@docusol.com",
        "usr_rol": "Radicador",
        "usr_sede": "Medellín",
        "usr_estado": "ACTIVO",
    },
    {
        "usr_id": 5,
        "usr_nombre": "Felipe Gestionador Medellín",
        "usr_email": "gestionador.medellin@docusol.com",
        "usr_rol": "Gestionador",
        "usr_sede": "Medellín",
        "usr_estado": "ACTIVO",
    },
    {
        "usr_id": 6,
        "usr_nombre": "Diana Radicadora Cali",
        "usr_email": "radicador.cali@docusol.com",
        "usr_rol": "Radicador",
        "usr_sede": "Cali",
        "usr_estado": "ACTIVO",
    },
    {
        "usr_id": 7,
        "usr_nombre": "Santiago Gestionador Cali",
        "usr_email": "gestionador.cali@docusol.com",
        "usr_rol": "Gestionador",
        "usr_sede": "Cali",
        "usr_estado": "ACTIVO",
    },
    {
        "usr_id": 8,
        "usr_nombre": "Sofía Administradora Medellín",
        "usr_email": "admin.medellin@docusol.com",
        "usr_rol": "Administrador",
        "usr_sede": "Medellín",
        "usr_estado": "ACTIVO",
    },
    {
        "usr_id": 9,
        "usr_nombre": "Julián Administrador Cali",
        "usr_email": "admin.cali@docusol.com",
        "usr_rol": "Administrador",
        "usr_sede": "Cali",
        "usr_estado": "ACTIVO",
    },
]

def run_sync():
    print("=" * 70)
    print(" DocuSol — Soluciones en Documentación | Sincronización Bcrypt")
    print("=" * 70)
    print(f"[*] Contraseña genérica de evaluación: {GENERIC_PASSWORD}")

    # Reintentos de conexión a MySQL
    max_retries = 15
    db = None
    for attempt in range(1, max_retries + 1):
        try:
            db = SessionLocal()
            # Probar consulta simple
            db.execute(Usuario.__table__.select().limit(1))
            print("[+] Conexión a la base de datos establecida exitosamente.")
            break
        except Exception as err:
            print(f"[-] Intento {attempt}/{max_retries}: Esperando MySQL... ({err})")
            time.sleep(2)
    else:
        print("[!] Error crítico: No fue posible conectar con MySQL.")
        sys.exit(1)

    try:
        # Generar hash bcrypt auténtico usando passlib
        print("[*] Generando hash Bcrypt con esquema passlib...")
        bcrypt_hash = get_password_hash(GENERIC_PASSWORD)
        print(f"[+] Hash generado: {bcrypt_hash}")

        # Comprobar validación de hash inmediatamente
        if not verify_password(GENERIC_PASSWORD, bcrypt_hash):
            print("[!] Error: La verificación del hash generado falló.")
            sys.exit(1)
        print("[+] Verificación interna de Bcrypt: OK.")

        # Actualizar usuarios existentes o insertar los oficiales si no existen
        actualizados = 0
        insertados = 0

        for user_data in USUARIOS_OFICIALES:
            # Buscar por email nuevo o por email antiguo (@nextgen.com) para migración transparente
            old_email = user_data["usr_email"].replace("@docusol.com", "@nextgen.com")
            usr = db.query(Usuario).filter(
                (Usuario.usr_email == user_data["usr_email"]) | (Usuario.usr_email == old_email)
            ).first()

            if usr:
                usr.usr_email = user_data["usr_email"]
                usr.usr_password_hash = bcrypt_hash
                usr.usr_estado = "ACTIVO"
                usr.usr_rol = user_data["usr_rol"]
                usr.usr_sede = user_data["usr_sede"]
                actualizados += 1
                print(f"  [ACTUALIZADO] {usr.usr_rol:14} | {usr.usr_email:30} | Sede: {usr.usr_sede}")
            else:
                nuevo = Usuario(
                    usr_id=user_data["usr_id"],
                    usr_nombre=user_data["usr_nombre"],
                    usr_email=user_data["usr_email"],
                    usr_password_hash=bcrypt_hash,
                    usr_rol=user_data["usr_rol"],
                    usr_sede=user_data["usr_sede"],
                    usr_estado="ACTIVO",
                )
                db.add(nuevo)
                insertados += 1
                print(f"  [INSERTADO]   {nuevo.usr_rol:14} | {nuevo.usr_email:30} | Sede: {nuevo.usr_sede}")

        # También actualizar cualquier otro usuario activo adicional que pudiera existir en la tabla
        otros_usuarios = db.query(Usuario).filter(
            ~Usuario.usr_email.in_([u["usr_email"] for u in USUARIOS_OFICIALES])
        ).all()
        for otro in otros_usuarios:
            otro.usr_password_hash = bcrypt_hash
            actualizados += 1
            print(f"  [ACTUALIZADO] {otro.usr_rol:14} | {otro.usr_email:30} | Sede: {otro.usr_sede}")

        db.commit()
        print("=" * 70)
        print(f"[✓] Éxito: {actualizados} usuarios actualizados, {insertados} usuarios creados.")
        print(f"[✓] Todas las cuentas están configuradas con contraseña: '{GENERIC_PASSWORD}'")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"[!] Error durante la sincronización: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_sync()
