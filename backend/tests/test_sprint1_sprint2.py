import io
import os
import sys
from pathlib import Path

# Permitir ejecución desde la raíz del proyecto
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ["TESTING"] = "1"

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.models.usuario import Usuario
from app.models.radicado import Radicado
from app.models.historial_aceptacion import HistorialAceptacion
from app.models.historial_cierre import HistorialCierre
from app.security.hashing import get_password_hash
from app.utils.business_days import sumar_dias_habiles_colombianos

# Configurar base de datos SQLite en memoria para pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_hu003_plazo_cuenta_dias_habiles_y_festivos_colombianos():
    inicio = datetime(2026, 10, 9, 14, 30)
    assert sumar_dias_habiles_colombianos(inicio, 1) == datetime(2026, 10, 13, 14, 30)
    assert sumar_dias_habiles_colombianos(inicio, 5) == datetime(2026, 10, 19, 14, 30)

@pytest.fixture(autouse=True, scope="module")
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine_test)
    db = TestingSessionLocal()


    # Sembrar usuarios iniciales
    hashed_pwd = get_password_hash("Password123!")
    usuarios = [
        Usuario(usr_id=1, usr_nombre="Carlos Admin", usr_email="admin@docusol.com", usr_password_hash=hashed_pwd, usr_rol="Administrador", usr_sede="Bogotá", usr_estado="ACTIVO"),
        Usuario(usr_id=2, usr_nombre="Laura Radicadora Bogotá", usr_email="radicador.bogota@docusol.com", usr_password_hash=hashed_pwd, usr_rol="Radicador", usr_sede="Bogotá", usr_estado="ACTIVO"),
        Usuario(usr_id=3, usr_nombre="Andrés Gestionador Bogotá", usr_email="gestionador.bogota@docusol.com", usr_password_hash=hashed_pwd, usr_rol="Gestionador", usr_sede="Bogotá", usr_estado="ACTIVO"),
        Usuario(usr_id=4, usr_nombre="Felipe Gestionador Medellín", usr_email="gestionador.medellin@docusol.com", usr_password_hash=hashed_pwd, usr_rol="Gestionador", usr_sede="Medellín", usr_estado="ACTIVO"),
        Usuario(usr_id=5, usr_nombre="Sofía Administradora Medellín", usr_email="admin.medellin@docusol.com", usr_password_hash=hashed_pwd, usr_rol="Administrador", usr_sede="Medellín", usr_estado="ACTIVO"),
        Usuario(usr_id=6, usr_nombre="Marta Radicadora Medellín", usr_email="radicador.medellin@docusol.com", usr_password_hash=hashed_pwd, usr_rol="Radicador", usr_sede="Medellín", usr_estado="ACTIVO"),
        Usuario(usr_id=7, usr_nombre="Julián Administrador Cali", usr_email="admin.cali@docusol.com", usr_password_hash=hashed_pwd, usr_rol="Administrador", usr_sede="Cali", usr_estado="ACTIVO"),
        Usuario(usr_id=8, usr_nombre="Diana Radicadora Cali", usr_email="radicador.cali@docusol.com", usr_password_hash=hashed_pwd, usr_rol="Radicador", usr_sede="Cali", usr_estado="ACTIVO"),
        Usuario(usr_id=9, usr_nombre="Santiago Gestionador Cali", usr_email="gestionador.cali@docusol.com", usr_password_hash=hashed_pwd, usr_rol="Gestionador", usr_sede="Cali", usr_estado="ACTIVO"),
    ]
    db.add_all(usuarios)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine_test)

def get_auth_token(email, password="Password123!"):
    db = TestingSessionLocal()
    usuario = db.query(Usuario).filter(Usuario.usr_email == email).first()
    sede = usuario.usr_sede if usuario else "Bogotá"
    db.close()
    res = client.post("/api/auth/login", json={"user_email": email, "user_password": password, "sede": sede})
    if res.status_code == 200:
        return res.json()["access_token"]
    return None

# ==============================================================================
# PRUEBAS SPRINT 1 (HU001 - HU005)
# ==============================================================================

def test_hu001_login_exitoso():
    res = client.post("/api/auth/login", json={"user_email": "admin@docusol.com", "user_password": "Password123!", "sede": "Bogotá"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["usuario"]["usr_rol"] == "Administrador"

def test_hu001_login_todos_los_roles():
    """Verifica autenticación exitosa para Admin, Radicador y Gestionador"""
    roles = [
        ("admin@docusol.com", "Administrador", "Bogotá"),
        ("radicador.bogota@docusol.com", "Radicador", "Bogotá"),
        ("gestionador.bogota@docusol.com", "Gestionador", "Bogotá"),
    ]
    for email, rol, sede in roles:
        res = client.post("/api/auth/login", json={"user_email": email, "user_password": "Password123!", "sede": sede})
        assert res.status_code == 200, f"Fallo al autenticar {email}"
        data = res.json()
        assert data["usuario"]["usr_rol"] == rol
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

def test_hu001_endpoint_token_oauth2():
    """Verifica compatibilidad con endpoint /token en formato form-data y JSON"""
    # Form-data
    res_form = client.post("/token", data={"username": "admin@docusol.com", "password": "Password123!", "sede": "Bogotá"})
    assert res_form.status_code == 200
    assert "access_token" in res_form.json()

    # JSON
    res_json = client.post("/token", json={"username": "gestionador.bogota@docusol.com", "password": "Password123!", "sede": "Bogotá"})
    assert res_json.status_code == 200
    assert "access_token" in res_json.json()

def test_hu001_login_credenciales_invalidas():
    res = client.post("/api/auth/login", json={"user_email": "admin@docusol.com", "user_password": "WrongPassword", "sede": "Bogotá"})
    assert res.status_code == 401
    # Criterio C.A.5: Mensaje exacto
    assert res.json()["detail"] == "Credenciales de acceso no válidas. Por favor verifique su correo y contraseña."

def test_hu001_login_rechaza_sede_incorrecta():
    res = client.post("/api/auth/login", json={
        "user_email": "radicador.bogota@docusol.com",
        "user_password": "Password123!",
        "sede": "Medellín"
    })
    assert res.status_code == 403
    assert res.json()["detail"] == "Solo se admiten correos dirigidos a la sede Medellín."

@pytest.mark.parametrize("email, rol, sede", [
    ("admin@docusol.com", "Administrador", "Bogotá"),
    ("radicador.bogota@docusol.com", "Radicador", "Bogotá"),
    ("gestionador.bogota@docusol.com", "Gestionador", "Bogotá"),
    ("admin.medellin@docusol.com", "Administrador", "Medellín"),
    ("radicador.medellin@docusol.com", "Radicador", "Medellín"),
    ("gestionador.medellin@docusol.com", "Gestionador", "Medellín"),
    ("admin.cali@docusol.com", "Administrador", "Cali"),
    ("radicador.cali@docusol.com", "Radicador", "Cali"),
    ("gestionador.cali@docusol.com", "Gestionador", "Cali"),
])
def test_hu001_login_todos_los_perfiles_por_sede(email, rol, sede):
    res = client.post("/api/auth/login", json={
        "user_email": email,
        "user_password": "Password123!",
        "sede": sede
    })
    assert res.status_code == 200
    assert res.json()["usuario"]["usr_rol"] == rol
    assert res.json()["usuario"]["usr_sede"] == sede

@pytest.mark.parametrize("email, sede", [
    ("admin@docusol.com", "Medellín"),
    ("admin.medellin@docusol.com", "Cali"),
    ("admin.cali@docusol.com", "Bogotá"),
])
def test_hu001_rechaza_login_en_sede_distinta(email, sede):
    res = client.post("/api/auth/login", json={
        "user_email": email,
        "user_password": "Password123!",
        "sede": sede
    })
    assert res.status_code == 403
    assert res.json()["detail"] == f"Solo se admiten correos dirigidos a la sede {sede}."

def test_hu002_listar_usuarios():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/usuarios", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 9
    assert {usuario["usr_sede"] for usuario in res.json()} == {"Bogotá", "Medellín", "Cali"}

def test_hu002_crear_usuario_exitoso():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "txt_nombre": "Nuevo Usuario Bogotá",
        "txt_email": "nuevo.bogota@docusol.com",
        "cmb_rol": "Gestionador",
        "cmb_sede": "Bogotá",
        "usr_password": "Password123!"
    }
    res = client.post("/api/usuarios", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["mensaje"] == "Usuario registrado exitosamente."
    assert data["usuario"]["usr_estado"] == "ACTIVO"
    assert data["usuario"]["usr_sede"] == "Bogotá"

def test_hu002_admin_asigna_cuentas_a_cualquier_sede():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "txt_nombre": "Usuario Medellín",
        "txt_email": "nuevo.medellin@docusol.com",
        "cmb_rol": "Radicador",
        "cmb_sede": "Medellín",
        "usr_password": "Password123!"
    }
    res = client.post("/api/usuarios", json=payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["usuario"]["usr_sede"] == "Medellín"

def test_hu002_registro_desde_acceso_exige_admin_de_la_misma_sede():
    payload = {
        "txt_nombre": "Usuario Bogotá",
        "txt_email": "registro.bogota@docusol.com",
        "cmb_rol": "Radicador",
        "usr_password": "Password123!",
        "admin_email": "admin@docusol.com",
        "admin_password": "Password123!"
    }
    res = client.post("/api/usuarios/registro/bogota", json=payload)
    assert res.status_code == 201
    assert res.json()["usuario"]["usr_sede"] == "Bogotá"

    res_cross_site = client.post("/api/usuarios/registro/medellin", json=payload)
    assert res_cross_site.status_code == 403

@pytest.mark.parametrize("sede_slug, sede, admin_email", [
    ("medellin", "Medellín", "admin.medellin@docusol.com"),
    ("cali", "Cali", "admin.cali@docusol.com"),
])
def test_hu002_admin_crea_cuenta_en_su_sede(sede_slug, sede, admin_email):
    payload = {
        "txt_nombre": f"Cuenta nueva {sede}",
        "txt_email": f"cuenta.nueva.{sede_slug}@docusol.com",
        "cmb_rol": "Gestionador",
        "usr_password": "Password123!",
        "admin_email": admin_email,
        "admin_password": "Password123!"
    }
    res = client.post(f"/api/usuarios/registro/{sede_slug}", json=payload)
    assert res.status_code == 201
    assert res.json()["usuario"]["usr_sede"] == sede

def test_hu002_crear_usuario_correo_duplicado():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "txt_nombre": "Duplicado",
        "txt_email": "admin@docusol.com",
        "cmb_rol": "Administrador",
        "cmb_sede": "Bogotá"
    }
    res = client.post("/api/usuarios", json=payload, headers=headers)
    assert res.status_code == 400
    assert res.json()["detail"] == "El correo corporativo ya se encuentra registrado en la base de datos."

def test_hu003_radicacion_campos_obligatorios_vacios():
    token = get_auth_token("radicador.bogota@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "txt_remitente": "",
        "txt_asunto": "Asunto de prueba",
        "cmb_tipo_doc": "Oficio",
        "cmb_sede_destino": "Medellín"
    }
    res = client.post("/api/radicados", json=payload, headers=headers)
    assert res.status_code == 400
    assert res.json()["detail"] == "Por favor complete todos los campos obligatorios antes de continuar."

def test_hu003_radicacion_exitosa():
    token = get_auth_token("radicador.bogota@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "txt_remitente": "Juzgado 1 Civil",
        "txt_asunto": "Acción de Tutela No. 450",
        "cmb_tipo_doc": "Tutela",
        "cmb_sede_destino": "Bogotá"
    }
    res = client.post("/api/radicados", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert "RAD-2026-" in data["mensaje"]
    assert data["radicado"]["rad_estado"] == "RADICADO"
    assert data["radicado"]["rad_codigo"].startswith("RAD-")

def test_hu003_radicado_no_visible_desde_otra_sede():
    token = get_auth_token("radicador.medellin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/radicados/1", headers=headers)
    assert res.status_code == 404

def test_hu003_radicado_se_enruta_a_la_sede_destino_indicada():
    """
    Propuesta Comercial (Perfil Radicador): el radicador "asigna el documento a
    una sede/destinatario" y ejecuta el "enrutamiento inicial hacia la sede y
    dependencia de destino". Un radicado dirigido a Medellin queda en Medellin
    en estado TRASLADADO, a la espera de la aceptacion de su gestionador.
    """
    token = get_auth_token("radicador.bogota@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "txt_remitente": "Entidad de Medellín",
        "txt_asunto": "Documento dirigido a Medellín",
        "cmb_tipo_doc": "Oficio",
        "cmb_sede_destino": "Medellín"
    }
    res = client.post("/api/radicados", json=payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["radicado"]["rad_sede_actual"] == "Medellín"
    assert res.json()["radicado"]["rad_sede_destino"] == "Medellín"
    assert res.json()["radicado"]["rad_sede_origen"] == "Bogotá"
    assert res.json()["radicado"]["rad_estado"] == "TRASLADADO"

    # El expediente ya no es visible para el radicador de la sede origen.
    rad_id = res.json()["radicado"]["rad_id"]
    assert client.get(f"/api/radicados/{rad_id}", headers=headers).status_code == 404

    # Y aparece en la bandeja de pendientes del gestionador de destino.
    token_med = get_auth_token("gestionador.medellin@docusol.com")
    pend = client.get("/api/recepcion/pendientes",
                      headers={"Authorization": f"Bearer {token_med}"})
    assert any(p["rad_id"] == rad_id for p in pend.json())


def test_hu003_radicado_en_sede_propia_queda_radicado():
    """Si la sede destino es la del radicador, el expediente se queda en RADICADO."""
    token = get_auth_token("radicador.bogota@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "txt_remitente": "Vecino de Bogotá",
        "txt_asunto": "Trámite en la propia sede",
        "cmb_tipo_doc": "Oficio",
        "cmb_sede_destino": "Bogotá"
    }
    res = client.post("/api/radicados", json=payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["radicado"]["rad_sede_actual"] == "Bogotá"
    assert res.json()["radicado"]["rad_estado"] == "RADICADO"

def test_hu004_carga_anexo_no_pdf():
    token = get_auth_token("radicador.bogota@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    # Enviar archivo .txt o .docx
    files = {"file_adjunto": ("documento.docx", b"dummy binary data", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"rad_id": 1}
    res = client.post("/api/anexos/subir", data=data, files=files, headers=headers)
    assert res.status_code == 400
    assert res.json()["detail"] == "Formato o tamaño de archivo no permitido. Solo se aceptan documentos PDF de hasta 15MB."

def test_hu004_carga_anexo_pdf_exitoso():
    token = get_auth_token("radicador.bogota@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    pdf_content = b"%PDF-1.4 dummy pdf content for testing"
    files = {"file_adjunto": ("memorial.pdf", pdf_content, "application/pdf")}
    data = {"rad_id": 1}
    res = client.post("/api/anexos/subir", data=data, files=files, headers=headers)
    assert res.status_code == 201
    assert res.json()["mensaje"] == "Archivo adjuntado correctamente al radicado."

def test_hu005_traslado_motivo_vacio():
    token = get_auth_token("radicador.bogota@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "rad_id": 1,
        "cmb_nueva_sede": "Medellín",
        "txt_motivo_traslado": ""
    }
    res = client.post("/api/traslados", json=payload, headers=headers)
    assert res.status_code == 400
    assert res.json()["detail"] == "Debe ingresar el motivo o justificación del traslado inter-sede."

def test_hu005_traslado_exitoso():
    token = get_auth_token("radicador.bogota@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "rad_id": 1,
        "cmb_nueva_sede": "Medellín",
        "txt_motivo_traslado": "Por competencia territorial corresponde a la sede de Medellín."
    }
    res = client.post("/api/traslados", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["mensaje"] == "El expediente ha sido trasladado exitosamente a la sede seleccionada."

def test_hu006_otra_sede_no_puede_aceptar_el_expediente():
    token = get_auth_token("gestionador.bogota@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/api/recepcion/aceptar/1", headers=headers)
    assert res.status_code == 404

# ==============================================================================
# PRUEBAS SPRINT 2 (HU006 - HU010)
# ==============================================================================

def test_hu006_recepcion_pendientes_y_aceptacion():
    # El radicado 1 fue trasladado a Medellín.
    # Ingresamos como gestionador de Medellín
    token = get_auth_token("gestionador.medellin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}

    # C.A.1: Consultar bandeja de pendientes
    res_pendientes = client.get("/api/recepcion/pendientes", headers=headers)
    assert res_pendientes.status_code == 200
    pendientes = res_pendientes.json()
    assert any(p["rad_id"] == 1 for p in pendientes)

    # C.A.2 & C.A.3: Aceptar radicado
    res_aceptar = client.post("/api/recepcion/aceptar/1", headers=headers)
    assert res_aceptar.status_code == 200
    assert res_aceptar.json()["mensaje"] == "Expediente aceptado correctamente. Asignado a su bandeja de gestión."

    # C.A.4: Debe desaparecer de pendientes y pasar a en_gestion
    res_pendientes_after = client.get("/api/recepcion/pendientes", headers=headers)
    assert not any(p["rad_id"] == 1 for p in res_pendientes_after.json())

    res_en_gestion = client.get("/api/recepcion/en_gestion", headers=headers)
    assert any(p["rad_id"] == 1 for p in res_en_gestion.json())
    db = TestingSessionLocal()
    aceptacion = db.query(HistorialAceptacion).filter(HistorialAceptacion.acep_rad_id == 1).one()
    db.close()
    assert aceptacion.acep_usuario_id == 4
    assert aceptacion.acep_sede == "Medellín"
    assert aceptacion.acep_fecha_hora is not None

def test_hu007_cierre_campos_vacios():
    token = get_auth_token("gestionador.medellin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    # Sin archivo ni observaciones
    data = {"rad_id": 1, "txt_observacion_cierre": ""}
    res = client.post("/api/cierre", data=data, headers=headers)
    assert res.status_code == 400
    assert res.json()["detail"] == "Es obligatorio adjuntar el documento de respuesta en PDF y detallar las observaciones de cierre."

def test_hu007_administrador_consulta_cierre_de_otra_sede():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/cierre/1", headers=headers)
    assert res.status_code == 200
    assert res.json()["radicado"]["rad_sede_actual"] == "Medellín"

def test_hu007_cierre_exitoso():
    token = get_auth_token("gestionador.medellin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    pdf_content = b"%PDF-1.4 dummy final response document"
    files = {"file_respuesta": ("respuesta_final.pdf", pdf_content, "application/pdf")}
    data = {"rad_id": 1, "txt_observacion_cierre": "Se da respuesta oportuna y completa al solicitante."}
    res = client.post("/api/cierre", data=data, files=files, headers=headers)
    assert res.status_code == 200
    assert res.json()["mensaje"] == "Trámite finalizado exitosamente. El expediente ha sido cerrado."
    assert res.json()["radicado"]["rad_estado"] == "FINALIZADO"
    db = TestingSessionLocal()
    evento_cierre = db.query(HistorialCierre).filter(HistorialCierre.cierre_rad_id == 1).one()
    db.close()
    assert evento_cierre.cierre_usuario_id == 4
    assert evento_cierre.cierre_sede == "Medellín"

def test_hu007_cierre_de_admin_guarda_el_actor_real():
    token = get_auth_token("admin.cali@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    pdf_content = b"%PDF-1.4 admin closure"
    files = {"file_respuesta": ("respuesta_admin.pdf", pdf_content, "application/pdf")}
    data = {"rad_id": 2, "txt_observacion_cierre": "Cierre autorizado por administración."}
    res = client.post("/api/cierre", data=data, files=files, headers=headers)
    assert res.status_code == 200
    db = TestingSessionLocal()
    evento_cierre = db.query(HistorialCierre).filter(HistorialCierre.cierre_rad_id == 2).one()
    db.close()
    assert evento_cierre.cierre_usuario_id == 7
    assert evento_cierre.cierre_sede == "Cali"

def test_hu008_auditoria_radicado_inexistente():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/auditoria/trazabilidad/RAD-2026-99999", headers=headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "El número de radicado ingresado no existe en el sistema."

def test_hu008_auditoria_trazabilidad_cronologica():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    # Consultar trazabilidad de radicado existente
    db = TestingSessionLocal()
    codigo = db.query(Radicado).filter(Radicado.rad_id == 1).first().rad_codigo
    db.close()
    res = client.get(f"/api/auditoria/trazabilidad/{codigo}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["linea_tiempo"]) >= 3
    evento_aceptacion = next(evento for evento in data["linea_tiempo"] if evento["estado"] == "ACEPTADO")
    db = TestingSessionLocal()
    aceptacion = db.query(HistorialAceptacion).filter(HistorialAceptacion.acep_rad_id == 1).one()
    db.close()
    assert evento_aceptacion["fecha_hora"] == aceptacion.acep_fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
    # Verificar columnas requeridas
    primer_evento = data["linea_tiempo"][0]
    assert "fecha_hora" in primer_evento
    assert "usuario" in primer_evento
    assert "sede_origen" in primer_evento
    assert "sede_destino" in primer_evento
    assert "accion_realizada" in primer_evento
    assert "estado" in primer_evento

def test_hu008_administrador_de_otra_sede_consulta_trazabilidad():
    token = get_auth_token("admin.cali@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    db = TestingSessionLocal()
    codigo = db.query(Radicado).filter(Radicado.rad_id == 1).first().rad_codigo
    db.close()
    res = client.get(f"/api/auditoria/trazabilidad/{codigo}", headers=headers)
    assert res.status_code == 200

def test_hu008_traza_registra_origen_y_destino_de_radicacion():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    db = TestingSessionLocal()
    codigo = db.query(Radicado).filter(Radicado.rad_id == 2).first().rad_codigo
    db.close()
    res = client.get(f"/api/auditoria/trazabilidad/{codigo}", headers=headers)
    assert res.status_code == 200
    evento_inicial = res.json()["linea_tiempo"][0]
    assert evento_inicial["sede_origen"] == "Bogotá"
    assert evento_inicial["sede_destino"] == "Medellín"
    evento_cierre = next(evento for evento in res.json()["linea_tiempo"] if evento["estado"] == "FINALIZADO")
    assert evento_cierre["usuario"] == "Julián Administrador Cali"

def test_hu009_reporte_fechas_incoherentes():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "dtp_fecha_inicio": "2026-12-31",
        "dtp_fecha_fin": "2026-01-01"
    }
    res = client.get("/api/reportes", params=params, headers=headers)
    assert res.status_code == 400
    assert res.json()["detail"] == "Rango de fechas incoherente. La fecha final no puede ser anterior a la inicial."

def test_hu009_reporte_y_exportar_excel():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "txt_remitente": "Reporte HU-009",
        "txt_asunto": "Radicado local para reporte",
        "cmb_tipo_doc": "Oficio",
        "cmb_sede_destino": "Bogotá"
    }
    res_crear = client.post("/api/radicados", json=payload, headers=headers)
    assert res_crear.status_code == 201

    token_medellin = get_auth_token("radicador.medellin@docusol.com")
    headers_medellin = {"Authorization": f"Bearer {token_medellin}"}
    res_crear_medellin = client.post("/api/radicados", json={
        "txt_remitente": "Reporte sede Medellín",
        "txt_asunto": "Registro para validar filtro global",
        "cmb_tipo_doc": "Oficio",
        "cmb_sede_destino": "Medellín"
    }, headers=headers_medellin)
    assert res_crear_medellin.status_code == 201

    res_filtro_medellin = client.get(
        "/api/reportes",
        params={"cmb_filtro_sede": "Medellín"},
        headers=headers
    )
    assert res_filtro_medellin.status_code == 200
    assert any(item["rad_sede_actual"] == "Medellín" for item in res_filtro_medellin.json())
    res = client.get("/api/reportes", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Exportar Excel
    res_excel = client.get("/api/reportes/exportar-excel", headers=headers)
    assert res_excel.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res_excel.headers["content-type"]

def test_hu010_dashboard_vencimientos():
    token = get_auth_token("admin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    token_cali = get_auth_token("radicador.cali@docusol.com")
    headers_cali = {"Authorization": f"Bearer {token_cali}"}
    res_crear = client.post("/api/radicados", json={
        "txt_remitente": "Dashboard sede Cali",
        "txt_asunto": "Registro activo para validar dashboard global",
        "cmb_tipo_doc": "Oficio",
        "cmb_sede_destino": "Cali"
    }, headers=headers_cali)
    assert res_crear.status_code == 201
    res = client.get("/api/dashboard/vencimientos", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_criticos" in data
    assert "total_atencion" in data
    assert "total_en_tiempo" in data
    assert "grid_criticos" in data
    todos_los_radicados = data["grid_criticos"] + data["grid_atencion"] + data["grid_en_tiempo"]
    assert any(item["rad_sede_actual"] == "Cali" for item in todos_los_radicados)

def test_hu010_gestionador_solo_ve_radicados_asignados():
    db = TestingSessionLocal()
    ahora = datetime.now()
    asignado = Radicado(
        rad_codigo="RAD-2026-GEST-ASIGNADO",
        rad_remitente="Juzgado de Medellín",
        rad_asunto="Expediente asignado",
        rad_tipo_doc="Oficio",
        rad_sede_destino="Medellín",
        rad_sede_actual="Medellín",
        rad_estado="ACEPTADO",
        rad_usuario_radicador=6,
        rad_usuario_gestionador=4,
        rad_fecha_creacion=ahora,
        rad_fecha_limite=ahora + timedelta(hours=12)
    )
    sin_asignar = Radicado(
        rad_codigo="RAD-2026-GEST-SIN-ASIGNAR",
        rad_remitente="Juzgado de Medellín",
        rad_asunto="Expediente pendiente",
        rad_tipo_doc="Oficio",
        rad_sede_destino="Medellín",
        rad_sede_actual="Medellín",
        rad_estado="RADICADO",
        rad_usuario_radicador=6,
        rad_usuario_gestionador=None,
        rad_fecha_creacion=ahora,
        rad_fecha_limite=ahora + timedelta(hours=12)
    )
    db.add_all([asignado, sin_asignar])
    db.commit()
    asignado_id = asignado.rad_id
    sin_asignar_id = sin_asignar.rad_id
    db.close()

    token = get_auth_token("gestionador.medellin@docusol.com")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/dashboard/vencimientos", headers=headers)
    assert res.status_code == 200
    dashboard_ids = {
        item["rad_id"]
        for grupo in ("grid_criticos", "grid_atencion", "grid_en_tiempo")
        for item in res.json()[grupo]
    }
    assert asignado_id in dashboard_ids
    assert sin_asignar_id not in dashboard_ids

# ==============================================================================
# PRUEBAS OPERATIVAS DEL GESTIONADOR Y STREAMING DE ADJUNTOS
# ==============================================================================

def test_streaming_pdf_anexo_y_radicado_con_bearer_y_query_param():
    token_bogota = get_auth_token("radicador.bogota@docusol.com")
    headers_bogota = {"Authorization": f"Bearer {token_bogota}"}

    # 1. Crear radicado en Bogotá
    res_crear = client.post("/api/radicados", json={
        "txt_remitente": "Tribunal Administrativo de Cundinamarca",
        "txt_asunto": "Acción constitucional con anexos de prueba",
        "cmb_tipo_doc": "Tutela",
        "cmb_sede_destino": "Bogotá"
    }, headers=headers_bogota)
    assert res_crear.status_code == 201
    rad_id = res_crear.json()["radicado"]["rad_id"]

    # 2. Adjuntar PDF
    pdf_content = b"%PDF-1.4 dummy test content for streaming"
    files = {"file_adjunto": ("tutela_expediente.pdf", pdf_content, "application/pdf")}
    res_subir = client.post("/api/anexos/subir", data={"rad_id": rad_id}, files=files, headers=headers_bogota)
    assert res_subir.status_code == 201
    anx_id = res_subir.json()["anexo"]["anx_id"]

    # 3. Streaming por anx_id con cabecera Bearer
    token_gest = get_auth_token("gestionador.bogota@docusol.com")
    res_stream_bearer = client.get(f"/api/anexos/archivo/{anx_id}", headers={"Authorization": f"Bearer {token_gest}"})
    assert res_stream_bearer.status_code == 200
    assert "application/pdf" in res_stream_bearer.headers.get("content-type", "")
    assert res_stream_bearer.content == pdf_content
    assert "tutela_expediente.pdf" in res_stream_bearer.headers.get("content-disposition", "")

    # 4. Streaming por anx_id con query param ?token=... (sin cabecera Authorization)
    res_stream_query = client.get(f"/api/anexos/archivo/{anx_id}?token={token_gest}")
    assert res_stream_query.status_code == 200
    assert "application/pdf" in res_stream_query.headers.get("content-type", "")
    assert res_stream_query.content == pdf_content

    # 5. Streaming por rad_id con cabecera Bearer
    res_rad_bearer = client.get(f"/api/anexos/radicado/{rad_id}/archivo", headers={"Authorization": f"Bearer {token_gest}"})
    assert res_rad_bearer.status_code == 200
    assert "application/pdf" in res_rad_bearer.headers.get("content-type", "")
    assert res_rad_bearer.content == pdf_content

    # 6. Streaming por rad_id con query param ?token=...
    res_rad_query = client.get(f"/api/anexos/radicado/{rad_id}/archivo?token={token_gest}")
    assert res_rad_query.status_code == 200
    assert "application/pdf" in res_rad_query.headers.get("content-type", "")
    assert res_rad_query.content == pdf_content

    # 7. Administrador puede consultar adjunto de cualquier sede
    token_admin = get_auth_token("admin@docusol.com")
    res_admin = client.get(f"/api/anexos/archivo/{anx_id}?token={token_admin}")
    assert res_admin.status_code == 200

def test_streaming_pdf_rechazo_archivo_inexistente_o_sede_distinta():
    token_bogota = get_auth_token("radicador.bogota@docusol.com")
    headers_bogota = {"Authorization": f"Bearer {token_bogota}"}

    # Crear radicado en Bogotá con anexo
    res_crear = client.post("/api/radicados", json={
        "txt_remitente": "Alcaldía Mayor de Bogotá",
        "txt_asunto": "Oficio restringido por sede",
        "cmb_tipo_doc": "Oficio",
        "cmb_sede_destino": "Bogotá"
    }, headers=headers_bogota)
    assert res_crear.status_code == 201
    rad_id = res_crear.json()["radicado"]["rad_id"]

    pdf_content = b"%PDF-1.4 restricted sede test"
    files = {"file_adjunto": ("restringido.pdf", pdf_content, "application/pdf")}
    res_subir = client.post("/api/anexos/subir", data={"rad_id": rad_id}, files=files, headers=headers_bogota)
    anx_id = res_subir.json()["anexo"]["anx_id"]

    # Anexo inexistente -> 404
    token_admin = get_auth_token("admin@docusol.com")
    res_no_anx = client.get("/api/anexos/archivo/999999", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_no_anx.status_code == 404

    # Radicado inexistente -> 404
    res_no_rad = client.get("/api/anexos/radicado/999999/archivo", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_no_rad.status_code == 404

    # Usuario de otra sede (Medellín) intentando acceder a radicado/anexo de Bogotá -> 404
    token_med = get_auth_token("gestionador.medellin@docusol.com")
    res_otra_sede_anx = client.get(f"/api/anexos/archivo/{anx_id}", headers={"Authorization": f"Bearer {token_med}"})
    assert res_otra_sede_anx.status_code == 404

    res_otra_sede_rad = client.get(f"/api/anexos/radicado/{rad_id}/archivo", headers={"Authorization": f"Bearer {token_med}"})
    assert res_otra_sede_rad.status_code == 404

    # Sin token / no autenticado -> 401
    res_unauth = client.get(f"/api/anexos/archivo/{anx_id}")
    assert res_unauth.status_code == 401

def test_visibilidad_y_aceptacion_radicado_en_bandeja_gestionador():
    # 1. Crear radicado en Bogotá que queda en estado RADICADO
    token_rad = get_auth_token("radicador.bogota@docusol.com")
    res_crear = client.post("/api/radicados", json={
        "txt_remitente": "Superintendencia de Sociedades",
        "txt_asunto": "Requerimiento de información financiera",
        "cmb_tipo_doc": "Requerimiento",
        "cmb_sede_destino": "Bogotá"
    }, headers={"Authorization": f"Bearer {token_rad}"})
    assert res_crear.status_code == 201
    rad_data = res_crear.json()["radicado"]
    rad_id = rad_data["rad_id"]
    assert rad_data["rad_estado"] == "RADICADO"
    assert rad_data["rad_sede_actual"] == "Bogotá"

    # 2. Gestionador Bogotá debe ver el radicado en su bandeja de pendientes
    token_gest = get_auth_token("gestionador.bogota@docusol.com")
    res_pendientes = client.get("/api/recepcion/pendientes", headers={"Authorization": f"Bearer {token_gest}"})
    assert res_pendientes.status_code == 200
    pendientes = res_pendientes.json()
    assert any(p["rad_id"] == rad_id and p["rad_estado"] == "RADICADO" for p in pendientes)

    # 3. Gestionador acepta el radicado
    res_aceptar = client.post(f"/api/recepcion/aceptar/{rad_id}", headers={"Authorization": f"Bearer {token_gest}"})
    assert res_aceptar.status_code == 200
    assert res_aceptar.json()["mensaje"] == "Expediente aceptado correctamente. Asignado a su bandeja de gestión."
    assert res_aceptar.json()["radicado"]["rad_estado"] == "ACEPTADO"

    # 4. Desaparece de pendientes y aparece en en_gestion
    res_pendientes_after = client.get("/api/recepcion/pendientes", headers={"Authorization": f"Bearer {token_gest}"})
    assert not any(p["rad_id"] == rad_id for p in res_pendientes_after.json())

    res_en_gestion = client.get("/api/recepcion/en_gestion", headers={"Authorization": f"Bearer {token_gest}"})
    assert any(g["rad_id"] == rad_id and g["rad_estado"] == "ACEPTADO" for g in res_en_gestion.json())

def test_traslado_inter_sedes_ejecutado_por_gestionador():
    token_rad = get_auth_token("radicador.bogota@docusol.com")
    res_crear = client.post("/api/radicados", json={
        "txt_remitente": "Procuraduría General de la Nación",
        "txt_asunto": "Expediente para traslado inter-sedes por gestionador",
        "cmb_tipo_doc": "Oficio",
        "cmb_sede_destino": "Bogotá"
    }, headers={"Authorization": f"Bearer {token_rad}"})
    assert res_crear.status_code == 201
    rad_id = res_crear.json()["radicado"]["rad_id"]

    # Gestionador Bogotá realiza traslado a Cali
    token_gest_bog = get_auth_token("gestionador.bogota@docusol.com")
    payload_traslado = {
        "rad_id": rad_id,
        "cmb_nueva_sede": "Cali",
        "txt_motivo_traslado": "Traslado de competencia remitido por el gestionador de Bogotá a la sede Cali."
    }
    res_traslado = client.post("/api/traslados", json=payload_traslado, headers={"Authorization": f"Bearer {token_gest_bog}"})
    assert res_traslado.status_code == 200
    assert res_traslado.json()["mensaje"] == "El expediente ha sido trasladado exitosamente a la sede seleccionada."

    # Gestionador Cali consulta pendientes y ve el radicado trasladado
    token_gest_cali = get_auth_token("gestionador.cali@docusol.com")
    res_pendientes_cali = client.get("/api/recepcion/pendientes", headers={"Authorization": f"Bearer {token_gest_cali}"})
    assert res_pendientes_cali.status_code == 200
    assert any(p["rad_id"] == rad_id and p["rad_estado"] == "TRASLADADO" and p["rad_sede_actual"] == "Cali" for p in res_pendientes_cali.json())

def test_administrador_respaldo_operativo_radicacion_y_anexos():
    token_admin = get_auth_token("admin@docusol.com")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    res_crear = client.post("/api/radicados", json={
        "txt_remitente": "Superintendencia de Notariado",
        "txt_asunto": "Radicación por respaldo operativo de Administrador",
        "cmb_tipo_doc": "Oficio",
        "cmb_sede_destino": "Medellín"
    }, headers=headers_admin)
    assert res_crear.status_code == 201
    rad_data = res_crear.json()["radicado"]
    rad_id = rad_data["rad_id"]

    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Respaldo) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    files = {"file_adjunto": ("adjunto_admin.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_anexo = client.post(
        "/api/anexos/subir",
        data={"rad_id": rad_id},
        files=files,
        headers=headers_admin
    )
    assert res_anexo.status_code == 201
    assert res_anexo.json()["mensaje"] == "Archivo adjuntado correctamente al radicado."

def test_administrador_respaldo_operativo_recepcion_aceptacion_y_cierre():
    token_rad_med = get_auth_token("radicador.medellin@docusol.com")
    headers_rad_med = {"Authorization": f"Bearer {token_rad_med}"}
    res_crear = client.post("/api/radicados", json={
        "txt_remitente": "Tribunal Superior de Medellín",
        "txt_asunto": "Caso para respaldo de gestión",
        "cmb_tipo_doc": "Tutela",
        "cmb_sede_destino": "Medellín"
    }, headers=headers_rad_med)
    assert res_crear.status_code == 201
    rad_id = res_crear.json()["radicado"]["rad_id"]

    token_admin = get_auth_token("admin@docusol.com")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    res_pendientes_all = client.get("/api/recepcion/pendientes?sede=Todas", headers=headers_admin)
    assert res_pendientes_all.status_code == 200
    assert any(p["rad_id"] == rad_id for p in res_pendientes_all.json())

    res_pendientes_med = client.get("/api/recepcion/pendientes?sede=Medellín", headers=headers_admin)
    assert res_pendientes_med.status_code == 200
    assert any(p["rad_id"] == rad_id for p in res_pendientes_med.json())

    res_aceptar = client.post(f"/api/recepcion/aceptar/{rad_id}", headers=headers_admin)
    assert res_aceptar.status_code == 200
    assert res_aceptar.json()["mensaje"] == "Expediente aceptado correctamente. Asignado a su bandeja de gestión."
    assert res_aceptar.json()["radicado"]["rad_estado"] == "ACEPTADO"

    res_en_gestion = client.get("/api/recepcion/en_gestion", headers=headers_admin)
    assert res_en_gestion.status_code == 200
    assert any(g["rad_id"] == rad_id for g in res_en_gestion.json())

    pdf_resp = b"%PDF-1.4\n1 0 obj\n<< /Title (Respuesta Admin) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    files = {"file_respuesta": ("respuesta_cierre_admin.pdf", io.BytesIO(pdf_resp), "application/pdf")}
    res_cierre = client.post(
        "/api/cierre",
        data={
            "rad_id": rad_id,
            "txt_observacion_cierre": "Cierre administrativo ejecutado como respaldo operativo ante ausencia temporal del gestionador titular."
        },
        files=files,
        headers=headers_admin
    )
    assert res_cierre.status_code == 200
    assert res_cierre.json()["mensaje"] == "Trámite finalizado exitosamente. El expediente ha sido cerrado."
    assert res_cierre.json()["radicado"]["rad_estado"] == "FINALIZADO"


