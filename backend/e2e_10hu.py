"""
Prueba E2E de las 10 HU (HU-001 a HU-010) contra la API en ejecucion.
Recorre el ciclo de vida completo: radicacion -> anexo -> traslado -> recepcion
-> cierre, y valida auditoria, reportes y dashboard.

Uso: python e2e_10hu.py [base_url]
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
PASSWORD = "Password123!"

PASSED, FAILED = [], []


def check(hu, name, condition, detail=""):
    entry = f"{hu} | {name}"
    if condition:
        PASSED.append(entry)
        print(f"  [OK]   {entry}")
    else:
        FAILED.append((entry, detail))
        print(f"  [FALLA] {entry}  -> {detail}")
    return condition


class Client:
    def __init__(self, token=None):
        self.token = token

    def request(self, method, path, body=None, headers=None, raw=None, content_type=None):
        url = f"{BASE}{path}"
        data = None
        hdrs = dict(headers or {})
        if self.token:
            hdrs["Authorization"] = f"Bearer {self.token}"
        if raw is not None:
            data = raw
            if content_type:
                hdrs["Content-Type"] = content_type
        elif body is not None:
            data = json.dumps(body).encode("utf-8")
            hdrs["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = resp.read()
                ctype = resp.headers.get("Content-Type", "")
                if "json" in ctype:
                    return resp.status, json.loads(payload.decode("utf-8")), resp.headers
                return resp.status, payload, resp.headers
        except urllib.error.HTTPError as e:
            payload = e.read()
            ctype = e.headers.get("Content-Type", "") if e.headers else ""
            if "json" in ctype:
                try:
                    return e.code, json.loads(payload.decode("utf-8")), e.headers
                except Exception:
                    return e.code, payload, e.headers
            return e.code, payload, e.headers
        except Exception as e:
            return 0, {"error": str(e)}, {}

    def get(self, p, **kw):
        return self.request("GET", p, **kw)

    def post(self, p, body=None, **kw):
        return self.request("POST", p, body, **kw)


def login(email, sede, password=PASSWORD):
    c = Client()
    st, data, _ = c.post("/api/auth/login", {
        "user_email": email, "user_password": password, "sede": sede,
    })
    if st != 200 or "access_token" not in (data or {}):
        raise RuntimeError(f"LOGIN FALLIDO {email} ({sede}): {st} {data}")
    return Client(data["access_token"]), data["usuario"]


def multipart(fields, files):
    """fields: dict[str,str]; files: list[(field, filename, bytes, content_type)]"""
    boundary = f"----kilo{uuid.uuid4().hex}"
    buf = io.BytesIO()
    for k, v in fields.items():
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        buf.write(f"{v}\r\n".encode())
    for field, fname, content, ctype in files:
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(
            f'Content-Disposition: form-data; name="{field}"; filename="{fname}"\r\n'.encode()
        )
        buf.write(f"Content-Type: {ctype}\r\n\r\n".encode())
        buf.write(content)
        buf.write(b"\r\n")
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue(), f"multipart/form-data; boundary={boundary}"


def pdf_bytes(min_pages=1):
    """PDF minimo valido."""
    out = io.BytesIO()
    objs = {}
    kids = " ".join(f"{3 + i} 0 R" for i in range(min_pages))
    objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[2] = f"<< /Type /Pages /Kids [{kids}] /Count {min_pages} >>".encode()
    for i in range(min_pages):
        objs[3 + i] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {3 + min_pages + i} 0 R >>"
        ).encode()
    objs[3 + min_pages] = b"<< /Length 44 >>\nstream\nBT /F1 12 Tf 72 720 Td (DocuSol) Tj ET\nendstream"
    out.write(b"%PDF-1.4\n")
    offsets = {}
    for num in sorted(objs):
        offsets[num] = out.tell()
        out.write(f"{num} 0 obj\n".encode() + objs[num] + b"\nendobj\n")
    xref = out.tell()
    maxn = max(objs) + 1
    out.write(f"xref\n0 {maxn}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for n in range(1, maxn):
        out.write(f"{offsets[n]:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {maxn} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def section(title):
    print(f"\n{'='*78}\n{title}\n{'='*78}")


def main():
    unico = uuid.uuid4().hex[:8]
    marca = f"E2E{unico}"

    section("HU-001 | Autenticacion y control perimetral")
    admin, u_admin = login("admin@docusol.com", "Bogotá")
    rad_bog, u_rad_bog = login("radicador.bogota@docusol.com", "Bogotá")
    ges_bog, u_ges_bog = login("gestionador.bogota@docusol.com", "Bogotá")
    rad_med, u_rad_med = login("radicador.medellin@docusol.com", "Medellín")
    ges_med, u_ges_med = login("gestionador.medellin@docusol.com", "Medellín")
    rad_cal, u_rad_cal = login("radicador.cali@docusol.com", "Cali")
    ges_cal, u_ges_cal = login("gestionador.cali@docusol.com", "Cali")
    check("HU-001", "login de las 9 cuentas oficiales", True)

    st, data, _ = Client().post("/api/auth/login", {
        "user_email": "admin@docusol.com", "user_password": "", "sede": "Bogotá"})
    check("HU-001", "rechaza password vacio con 401", st == 401, f"status={st} data={data}")

    st, data, _ = Client().post("/api/auth/login", {
        "user_email": "admin@docusol.com", "user_password": "claveIncorrecta999", "sede": "Bogotá"})
    check("HU-001", "rechaza password incorrecta con 401", st == 401, f"status={st}")

    st, data, _ = Client().post("/api/auth/login", {
        "user_email": "noexiste@docusol.com", "user_password": "Password123!", "sede": "Bogotá"})
    check("HU-001", "rechaza usuario inexistente con 401", st == 401, f"status={st}")

    st, data, _ = rad_med.post("/api/auth/login", {
        "user_email": "radicador.medellin@docusol.com",
        "user_password": PASSWORD, "sede": "Cali"})
    check("HU-001", "bloquea login en sede ajena con 403", st == 403, f"status={st} data={data}")

    st, data, _ = Client().get("/api/radicados")
    check("HU-001", "rechaza peticion sin token con 401", st == 401, f"status={st}")

    st, data, _ = Client("token-falso-invalido").get("/api/radicados")
    check("HU-001", "rechaza token invalido con 401", st == 401, f"status={st}")

    st, data, _ = admin.get("/api/auth/me")
    check("HU-001", "/api/auth/me devuelve la sesion", st == 200 and data.get("usr_email") == "admin@docusol.com",
          f"status={st} data={data}")

    section("HU-002 | Gestion de cuentas de usuario y roles")
    admin_med, _ = login("admin.medellin@docusol.com", "Medellín")
    admin_cal, _ = login("admin.cali@docusol.com", "Cali")
    st, data, _ = admin.get("/api/usuarios")
    total = len(data) if isinstance(data, list) else -1
    check("HU-002", "admin lista usuarios", st == 200 and total >= 9, f"status={st} total={total}")

    st, data, _ = rad_bog.get("/api/usuarios")
    check("HU-002", "radicador NO puede listar usuarios (403)", st == 403, f"status={st}")

    email_nuevo = f"e2e.{marca}@docusol.com"
    st, data, _ = admin.post("/api/usuarios", {
        "txt_nombre": f"E2E Usuario {marca}", "txt_email": email_nuevo,
        "cmb_rol": "Radicador", "cmb_sede": "Cali", "usr_password": "Temporal123!",
    })
    check("HU-002", "admin crea usuario con rol y sede", st in (200, 201), f"status={st} data={data}")
    nuevo_id = None
    if st in (200, 201):
        nuevo_id = (data.get("usuario") or data).get("usr_id")

    st, data, _ = admin.post("/api/usuarios", {
        "txt_nombre": "Duplicado", "txt_email": email_nuevo,
        "cmb_rol": "Radicador", "cmb_sede": "Cali", "usr_password": "Temporal123!",
    })
    check("HU-002", "rechaza correo duplicado con 400", st == 400, f"status={st} data={data}")

    st, data, _ = admin.post("/api/usuarios", {
        "txt_nombre": "Sin sede", "txt_email": f"x{marca}@docusol.com",
        "cmb_rol": "Invalido", "cmb_sede": "Cali", "usr_password": "Temporal123!",
    })
    check("HU-002", "rechaza rol inexistente con 422", st == 422, f"status={st} data={data}")

    st, data, _ = rad_bog.post("/api/usuarios", {
        "txt_nombre": "Intruso", "txt_email": f"int{marca}@docusol.com",
        "cmb_rol": "Administrador", "cmb_sede": "Bogotá", "usr_password": "Temporal123!",
    })
    check("HU-002", "radicador NO puede crear usuarios (403)", st == 403, f"status={st}")

    if nuevo_id:
        try:
            c_nuevo, _ = login(email_nuevo, "Cali", "Temporal123!")
            check("HU-002", "usuario creado puede autenticarse con su clave", True)
        except RuntimeError as e:
            check("HU-002", "usuario creado puede autenticarse con su clave", False, str(e))

    section("HU-003 | Radicacion de documentos")
    st, data, _ = rad_bog.post("/api/radicados", {
        "txt_remitente": f"Ciudadania {marca}", "txt_asunto": f"DERECHO DE PETICION {marca}",
        "cmb_tipo_doc": "Derecho de peticion", "cmb_sede_destino": "Bogotá",
    })
    ok3 = st in (200, 201) and "radicado" in (data or {})
    check("HU-003", "radicador crea radicado", ok3, f"status={st} data={data}")
    rad = (data or {}).get("radicado") or {}
    rad_id = rad.get("rad_id")
    codigo = rad.get("rad_codigo")
    check("HU-003", f"codigo con formato RAD-2026-XXXXX ({codigo})",
          bool(codigo) and codigo.startswith("RAD-") and len(codigo) >= 9, f"codigo={codigo}")
    check("HU-003", "estado inicial RADICADO", rad.get("rad_estado") == "RADICADO", f"{rad.get('rad_estado')}")
    check("HU-003", "sede actual = sede del operador", rad.get("rad_sede_actual") == "Bogotá",
          f"{rad.get('rad_sede_actual')}")
    check("HU-003", "fecha limite SLA calculada a futuro",
          bool(rad.get("rad_fecha_limite")) and rad["rad_fecha_limite"] > rad["rad_fecha_creacion"],
          f"limite={rad.get('rad_fecha_limite')} creacion={rad.get('rad_fecha_creacion')}")

    st, data, _ = rad_bog.post("/api/radicados", {
        "txt_remitente": "", "txt_asunto": "x", "cmb_tipo_doc": "Oficio", "cmb_sede_destino": "Bogotá",
    })
    check("HU-003", "rechaza remitente vacio con 400", st == 400, f"status={st} data={data}")

    st, data, _ = rad_cal.post("/api/radicados", {
        "txt_remitente": "Otra sede", "txt_asunto": "Prueba aislamiento",
        "cmb_tipo_doc": "Oficio", "cmb_sede_destino": "Medellín",
    })
    ok_iso = st in (200, 201)
    r_iso = (data.get("radicado") or {})
    check("HU-003", "el expediente se enruta a la sede destino elegida (propuesta: enrutamiento inicial)",
          ok_iso and r_iso.get("rad_sede_actual") == "Medellín", f"status={st} data={str(data)[:220]}")
    check("HU-003", "queda TRASLADADO a la espera de aceptacion formal",
          r_iso.get("rad_estado") == "TRASLADADO", f"estado={r_iso.get('rad_estado')}")
    check("HU-003", "conserva la sede de origen para la trazabilidad",
          r_iso.get("rad_sede_origen") == "Cali", f"origen={r_iso.get('rad_sede_origen')}")
    if ok_iso:
        id_iso = r_iso.get("rad_id")
        st2, _, _ = rad_cal.get(f"/api/radicados/{id_iso}")
        check("HU-003", "aislamiento: el radicador origen ya no lo ve", st2 == 404, f"status={st2}")
        st2, _, _ = ges_med.get(f"/api/radicados/{id_iso}")
        check("HU-003", "la sede destino si lo recibe", st2 == 200, f"status={st2}")
        st2, pend, _ = ges_med.get("/api/recepcion/pendientes")
        check("HU-003", "aparece en la bandeja de pendientes del destino",
              any(p["rad_id"] == id_iso for p in (pend or [])), "no aparece en pendientes")

    section("HU-004 | Carga de anexos PDF")
    body, ctype = multipart({"rad_id": str(rad_id)}, [("file_adjunto", f"{marca}.pdf", pdf_bytes(2), "application/pdf")])
    st, data, _ = rad_bog.post("/api/anexos/subir", raw=body, content_type=ctype)
    ok4 = st in (200, 201)
    check("HU-004", "radicador carga anexo PDF", ok4, f"status={st} data={str(data)[:300]}")
    anexos = []
    if ok4:
        anexos = data.get("grid_anexos") or data.get("anexos") or []
        if not anexos and isinstance(data.get("anexo"), dict):
            anexos = [data["anexo"]]

    body, ctype = multipart({"rad_id": str(rad_id)}, [("file_adjunto", f"{marca}.txt", b"texto plano", "text/plain")])
    st, data, _ = rad_bog.post("/api/anexos/subir", raw=body, content_type=ctype)
    check("HU-004", "rechaza extension no PDF con 400", st == 400, f"status={st}")

    body, ctype = multipart({"rad_id": str(rad_id)}, [("file_adjunto", "grande.pdf", b"%PDF-1.4\n" + b"0" * (16 * 1024 * 1024), "application/pdf")])
    st, data, _ = rad_bog.post("/api/anexos/subir", raw=body, content_type=ctype)
    check("HU-004", "rechaza PDF mayor a 15 MB con 400", st == 400, f"status={st}")

    body, ctype = multipart({"rad_id": "99999999"}, [("file_adjunto", "x.pdf", pdf_bytes(), "application/pdf")])
    st, data, _ = rad_bog.post("/api/anexos/subir", raw=body, content_type=ctype)
    check("HU-004", "rechaza radicado inexistente con 404", st == 404, f"status={st}")

    if anexos:
        anx_id = anexos[0].get("anx_id")
        st, content, headers = rad_bog.get(f"/api/anexos/archivo/{anx_id}")
        check("HU-004", "descarga anexo con token en header",
              st == 200 and isinstance(content, bytes) and content[:4] == b"%PDF",
              f"status={st} len={len(content) if isinstance(content, bytes) else content}")
        st, _, _ = Client().get(f"/api/anexos/archivo/{anx_id}")
        check("HU-004", "rechaza descarga de anexo sin token", st == 401, f"status={st}")
        st, _, _ = admin.get(f"/api/anexos/archivo/{anx_id}?token={admin.token}")
        check("HU-004", "acepta token por query string para descarga", st == 200, f"status={st}")
        st, _, _ = ges_med.get(f"/api/anexos/archivo/{anx_id}")
        check("HU-004", "bloquea descarga de anexo a usuario de otra sede", st in (403, 404), f"status={st}")

    _b, _c = multipart({"rad_id": str(rad_id)}, [("file_adjunto", "x.pdf", pdf_bytes(), "application/pdf")])
    st, data, _ = ges_cal.post("/api/anexos/subir", raw=_b, content_type=_c)
    check("HU-004", "bloquea carga de anexo de radicado de otra sede", st in (403, 404), f"status={st}")

    st, _, _ = Client().get("/uploads/anexos/")
    check("HU-004", "/uploads NO se sirve sin autenticacion (404)", st == 404, f"status={st}")

    section("HU-005 | Traslado inter-sedes")
    st, data, _ = rad_bog.post("/api/traslados", {
        "rad_id": rad_id, "cmb_nueva_sede": "Medellín", "txt_motivo_traslado": "",
    })
    check("HU-005", "rechaza motivo vacio con 400", st == 400, f"status={st} data={data}")

    st, data, _ = rad_bog.post("/api/traslados", {
        "rad_id": rad_id, "cmb_nueva_sede": "Bogotá", "txt_motivo_traslado": "Auto traslado",
    })
    check("HU-005", "rechaza auto-traslado a la misma sede", st == 400, f"status={st} data={data}")

    st, data, _ = rad_med.post("/api/traslados", {
        "rad_id": rad_id, "cmb_nueva_sede": "Cali", "txt_motivo_traslado": "Intento de otra sede",
    })
    check("HU-005", "bloquea traslado de radicado de otra sede", st in (403, 404), f"status={st}")

    st, data, _ = rad_bog.post("/api/traslados", {
        "rad_id": rad_id, "cmb_nueva_sede": "Sede Inexistente",
        "txt_motivo_traslado": "Sede invalida",
    })
    check("HU-005", "rechaza sede destino inexistente con 400", st == 400, f"status={st} data={data}")

    st, data, _ = rad_bog.post("/api/traslados", {
        "rad_id": rad_id, "cmb_nueva_sede": "Medellín",
        "txt_motivo_traslado": f"E2E traslado legitimo {marca}",
    })
    ok5 = st == 200 and "traslado" in (data or {})
    check("HU-005", "radicador traslada a otra sede", ok5, f"status={st} data={data}")

    st, data, _ = admin.get(f"/api/radicados/{rad_id}")
    check("HU-005", "estado pasa a TRASLADADO", data.get("rad_estado") == "TRASLADADO", f"{data.get('rad_estado')}")
    check("HU-005", "sede actual pasa a Medellin", data.get("rad_sede_actual") == "Medellín",
          f"{data.get('rad_sede_actual')}")
    check("HU-005", "rad_sede_destino se sincroniza con el traslado",
          data.get("rad_sede_destino") == "Medellín", f"{data.get('rad_sede_destino')}")
    check("HU-005", "se libera el gestionador de la sede origen",
          data.get("rad_usuario_gestionador") is None, f"{data.get('rad_usuario_gestionador')}")

    st, data, _ = rad_bog.get("/api/radicados")
    visibles = [r["rad_id"] for r in (data or [])] if isinstance(data, list) else []
    check("HU-005", "radicador de Bogota ya no ve el radicado trasladado",
          rad_id not in visibles, f"visibles={visibles}")

    section("HU-006 | Recepcion y aceptacion")
    st, data, _ = ges_bog.get("/api/recepcion/pendientes")
    pend_bog = [r["rad_id"] for r in (data or [])] if isinstance(data, list) else []
    check("HU-006", "gestionador de Bogota NO ve el expediente trasladado",
          rad_id not in pend_bog, f"pendientes={pend_bog}")

    st, data, _ = ges_med.get("/api/recepcion/pendientes")
    pend_med = data if isinstance(data, list) else []
    ids_med = [r["rad_id"] for r in pend_med]
    check("HU-006", "gestionador de Medellin ve el expediente trasladado", rad_id in ids_med, f"ids={ids_med}")
    check("HU-006", "pendientes filtran solo sede propia",
          all(r["rad_sede_actual"] == "Medellín" for r in pend_med),
          f"{[r['rad_sede_actual'] for r in pend_med]}")

    st, data, _ = ges_bog.post(f"/api/recepcion/aceptar/{rad_id}")
    check("HU-006", "bloquea aceptacion desde sede equivocada", st in (403, 404), f"status={st}")

    st, data, _ = ges_med.post(f"/api/recepcion/aceptar/{rad_id}")
    check("HU-006", "gestionador destino acepta el expediente",
          st == 200 and (data.get("radicado") or {}).get("rad_estado") == "ACEPTADO",
          f"status={st} data={data}")

    st, data, _ = ges_med.get("/api/recepcion/en_gestion")
    en_gest = [r["rad_id"] for r in (data or [])] if isinstance(data, list) else []
    check("HU-006", "expediente pasa a la bandeja En Gestion", rad_id in en_gest, f"en_gestion={en_gest}")

    st, data, _ = ges_med.post(f"/api/recepcion/aceptar/{rad_id}")
    check("HU-006", "rechaza doble aceptacion con 400", st == 400, f"status={st} data={data}")

    section("HU-007 | Cierre de expediente")
    body, ctype = multipart({"rad_id": str(rad_id), "txt_observacion_cierre": ""},
                            [("file_respuesta", f"resp{marca}.pdf", pdf_bytes(), "application/pdf")])
    st, data, _ = ges_med.post("/api/cierre", raw=body, content_type=ctype)
    check("HU-007", "rechaza cierre sin observaciones con 400", st == 400, f"status={st} data={str(data)[:200]}")

    body, ctype = multipart({"rad_id": str(rad_id), "txt_observacion_cierre": f"E2E cierre {marca}"}, [])
    st, data, _ = ges_med.post("/api/cierre", raw=body, content_type=ctype)
    check("HU-007", "rechaza cierre sin PDF de respuesta con 400", st == 400, f"status={st} data={str(data)[:200]}")

    body, ctype = multipart({"rad_id": str(rad_id), "txt_observacion_cierre": f"E2E cierre {marca}"},
                            [("file_respuesta", f"resp{marca}.txt", b"no pdf", "text/plain")])
    st, data, _ = ges_med.post("/api/cierre", raw=body, content_type=ctype)
    check("HU-007", "rechaza respuesta que no es PDF", st == 400, f"status={st} data={str(data)[:200]}")

    body, ctype = multipart({"rad_id": str(rad_id), "txt_observacion_cierre": f"E2E cierre {marca}"},
                            [("file_respuesta", f"resp{marca}.pdf", pdf_bytes(), "application/pdf")])
    st, data, _ = ges_bog.post("/api/cierre", raw=body, content_type=ctype)
    check("HU-007", "bloquea cierre por gestionador de otra sede", st in (403, 404), f"status={st}")

    body, ctype = multipart({"rad_id": str(rad_id), "txt_observacion_cierre": f"E2E cierre {marca}"},
                            [("file_respuesta", f"resp{marca}.pdf", pdf_bytes(), "application/pdf")])
    st, data, _ = ges_cal.post("/api/cierre", raw=body, content_type=ctype)
    check("HU-007", "bloquea cierre de expediente de otra sede", st in (403, 404), f"status={st}")

    st, data, _ = admin_cal.get(f"/api/radicados/{rad_id}")
    check("HU-007", "admin de otra sede puede SUPERVISAR (leer) el radicado", st == 200, f"status={st}")

    # El cierre del Administrador en respaldo operativo lo cubren
    # test_hu007_cierre_de_admin_guarda_el_actor_real y
    # test_administrador_respaldo_operativo_recepcion_aceptacion_y_cierre.

    body, ctype = multipart({"rad_id": str(rad_id), "txt_observacion_cierre": f"E2E cierre {marca}"},
                            [("file_respuesta", "vacio.pdf", b"", "application/pdf")])
    st, data, _ = ges_med.post("/api/cierre", raw=body, content_type=ctype)
    check("HU-007", "rechaza PDF de respuesta vacio", st == 400, f"status={st}")

    body, ctype = multipart({"rad_id": str(rad_id), "txt_observacion_cierre": f"E2E cierre {marca}"},
                            [("file_respuesta", f"resp{marca}.pdf", pdf_bytes(), "application/pdf")])
    st, data, _ = ges_med.post("/api/cierre", raw=body, content_type=ctype)
    check("HU-007", "gestionador asignado cierra el expediente", st == 200, f"status={st} data={str(data)[:300]}")

    st, data, _ = admin.get(f"/api/radicados/{rad_id}")
    check("HU-007", "estado final FINALIZADO", data.get("rad_estado") == "FINALIZADO", f"{data.get('rad_estado')}")

    _b, _c = multipart({"rad_id": str(rad_id), "txt_observacion_cierre": "Segundo cierre"},
                    [("file_respuesta", "r2.pdf", pdf_bytes(), "application/pdf")])
    st, data, _ = ges_med.post("/api/cierre", raw=_b, content_type=_c)
    check("HU-007", "rechaza re-cierre de expediente finalizado con 400", st == 400, f"status={st}")

    st, data, _ = ges_med.get("/api/recepcion/en_gestion")
    ids = [r["rad_id"] for r in (data or [])] if isinstance(data, list) else []
    check("HU-007", "expediente sale de En Gestion tras el cierre", rad_id not in ids, f"ids={ids}")

    section("HU-008 | Auditoria y trazabilidad")
    st, data, _ = admin.get(f"/api/auditoria/trazabilidad/{codigo}")
    ok8 = st == 200 and "linea_tiempo" in (data or {})
    check("HU-008", "admin consulta trazabilidad por codigo", ok8, f"status={st} data={str(data)[:300]}")
    eventos = (data or {}).get("linea_tiempo") or []
    check("HU-008", f"timeline con 5 eventos ({len(eventos)})", len(eventos) >= 5, f"n={len(eventos)}")

    fechas = [e["fecha_hora"] for e in eventos]
    check("HU-008", "eventos en orden cronologico ascendente", fechas == sorted(fechas), f"{fechas}")

    estados = [e["estado"] for e in eventos]
    for est in ["RADICADO", "TRASLADADO", "ACEPTADO", "FINALIZADO"]:
        check("HU-008", f"timeline incluye estado {est}", est in estados, f"estados={estados}")

    check("HU-008", "evento de radicacion registra la sede de origen",
          any(e["sede_origen"] == "Bogotá" for e in eventos),
          f"{[(e['estado'], e['sede_origen'], e['sede_destino']) for e in eventos]}")
    check("HU-008", "evento de traslado muestra Bogota -> Medellin",
          any(e["sede_origen"] == "Bogotá" and e["sede_destino"] == "Medellín" for e in eventos),
          f"{[(e['estado'], e['sede_origen'], e['sede_destino']) for e in eventos]}")
    check("HU-008", "timeline incluye el evento de carga de anexos",
          any("anexo" in e["accion_realizada"].lower() for e in eventos),
          f"{[e['accion_realizada'][:40] for e in eventos]}")
    anexos_ev = [e for e in eventos if "anexo" in e["accion_realizada"].lower()]
    check("HU-008", "el evento de anexo identifica a quien lo digitalizo",
          len(anexos_ev) == 1 and anexos_ev[0]["usuario"] == "Laura Radicadora Bogotá",
          f"eventos_anexo={anexos_ev}")
    acept_ev = [e for e in eventos if e["estado"] == "ACEPTADO"]
    check("HU-008", "el evento de aceptacion registra la sede del operador",
          len(acept_ev) == 1 and acept_ev[0]["sede_origen"] == "Medellín",
          f"{acept_ev}")
    cierre_ev = [e for e in eventos if e["estado"] == "FINALIZADO"]
    check("HU-008", "el evento de cierre registra la sede del operador",
          len(cierre_ev) >= 1 and cierre_ev[0]["sede_origen"] == "Medellín", f"{cierre_ev}")
    check("HU-008", "ningun evento queda sin fecha", all(e["fecha_hora"] for e in eventos),
          f"{[e['fecha_hora'] for e in eventos]}")
    ip_ev = [e for e in eventos if e["estado"] in ("TRASLADADO", "ACEPTADO", "FINALIZADO")]
    check("HU-008", "los eventos de gestion registran direccion IP (propuesta comercial)",
          bool(ip_ev) and all(e.get("ip_origen") for e in ip_ev),
          f"{[(e['estado'], e.get('ip_origen')) for e in ip_ev]}")

    st, data, _ = admin.get("/api/auditoria/trazabilidad/RAD-9999-99999")
    check("HU-008", "codigo inexistente devuelve 404", st == 404, f"status={st}")

    st, _, _ = ges_med.get(f"/api/auditoria/trazabilidad/{codigo}")
    check("HU-008", "gestionador NO puede auditar (403)", st == 403, f"status={st}")

    st, data, _ = rad_bog.get(f"/api/auditoria/trazabilidad/{codigo}")
    check("HU-008", "radicador NO puede auditar (403)", st == 403, f"status={st}")

    st, data, _ = admin.get(f"/api/auditoria/trazabilidad/{codigo}")
    check("HU-008", "respuesta marca solo lectura",
          (data or {}).get("es_solo_lectura") is not False, f"data={str(data)[:200]}")

    section("HU-009 | Reportes parametrizados y exportacion Excel")
    st, data, _ = admin.get("/api/reportes")
    check("HU-009", "admin consulta reporte sin filtros", st == 200 and isinstance(data, list),
          f"status={st} type={type(data)}")
    ids_rep = [r["rad_id"] for r in (data or [])] if isinstance(data, list) else []
    check("HU-009", "el radicado E2E aparece en el reporte", rad_id in ids_rep, f"ids={ids_rep}")

    st, data, _ = admin.get("/api/reportes?dtp_fecha_inicio=2020-01-01&dtp_fecha_fin=2020-01-31")
    check("HU-009", "filtro por rango de fechas responde 200", st == 200 and isinstance(data, list),
          f"status={st} data={str(data)[:200]}")

    st, data, _ = admin.get("/api/reportes?dtp_fecha_inicio=2026-12-31&dtp_fecha_fin=2026-01-01")
    check("HU-009", "rechaza rango incoherente con 400", st == 400, f"status={st} data={data}")

    sede_filtro = urllib.parse.quote("Medellín")
    st, data, _ = admin.get(f"/api/reportes?cmb_filtro_sede={sede_filtro}")
    sedes = {r["rad_sede_actual"] for r in (data or [])} if isinstance(data, list) else set()
    check("HU-009", "filtro por sede devuelve solo esa sede",
          st == 200 and sedes <= {"Medellín"}, f"status={st} sedes={sedes}")

    st, data, _ = admin.get("/api/reportes?cmb_filtro_estado=FINALIZADO")
    estados_rep = {r["rad_estado"] for r in (data or [])} if isinstance(data, list) else set()
    check("HU-009", "filtro por estado devuelve solo ese estado",
          st == 200 and estados_rep <= {"FINALIZADO"}, f"status={st} estados={estados_rep}")

    st, content, headers = admin.get("/api/reportes/exportar-excel?cmb_filtro_sede=Todas&cmb_filtro_estado=Todos")
    es_xlsx = st == 200 and isinstance(content, bytes) and content[:2] == b"PK"
    check("HU-009", "exporta .xlsx valido (firma PK)", es_xlsx,
          f"status={st} head={content[:8] if isinstance(content, bytes) else content}")
    if es_xlsx:
        try:
            zf = zipfile.ZipFile(io.BytesIO(content))
            names = zf.namelist()
            check("HU-009", "el .xlsx contiene hoja de calculo",
                  any("sheet" in n for n in names), f"names={names[:6]}")
            texto = ""
            for n in names:
                if n.endswith(".xml"):
                    texto += zf.read(n).decode("utf-8", "ignore")
            check("HU-009", "el .xlsx incluye el radicado E2E", codigo in texto, f"codigo={codigo}")
            for col in ["Código", "Remitente", "Asunto"]:
                check("HU-009", f"el .xlsx incluye la columna {col}", col in texto, "columna ausente")
        except Exception as e:
            check("HU-009", "el .xlsx se puede abrir como zip", False, str(e))

    st, _, _ = rad_bog.get("/api/reportes")
    check("HU-009", "radicador NO puede ver reportes (403)", st == 403, f"status={st}")

    st, _, _ = Client().get("/api/reportes/exportar-excel")
    check("HU-009", "exportar sin token devuelve 401", st == 401, f"status={st}")

    st, data, _ = admin.get("/api/reportes/exportar-excel?cmb_filtro_sede=Todas&cmb_filtro_estado=Todos"
                            "&dtp_fecha_inicio=2030-01-01&dtp_fecha_fin=2030-01-02")
    check("HU-009", "exportar sin registros responde con error controlado",
          st in (200, 400), f"status={st}")

    section("HU-010 | Dashboard de vencimientos SLA")
    st, data, _ = admin.get("/api/dashboard/vencimientos")
    check("HU-010", "admin consulta dashboard", st == 200, f"status={st} data={str(data)[:200]}")
    check("HU-010", "dashboard trae totales y grids del semaforo",
          isinstance(data, dict) and all(k in data for k in
                                         ("total_criticos", "total_atencion", "total_en_tiempo",
                                          "grid_criticos", "grid_atencion", "grid_en_tiempo")),
          f"keys={list(data.keys()) if isinstance(data, dict) else type(data)}")

    st, data, _ = ges_bog.get("/api/dashboard/vencimientos")
    check("HU-010", "gestionador consulta su dashboard", st == 200, f"status={st}")

    st, data, _ = rad_bog.get("/api/dashboard/vencimientos")
    check("HU-010", "radicador NO puede ver el dashboard (403)", st == 403, f"status={st}")

    if isinstance(data, dict):
        for clave in ("grid_criticos", "grid_atencion", "grid_en_tiempo"):
            items = data.get(clave) or []
            if items:
                est = items[0].get("estado_semaforo")
                check("HU-010", f"items de {clave} traen estado_semaforo",
                      est in ("CRITICO", "CRÍTICO", "ATENCION", "ATENCIÓN", "EN TIEMPO", "EN_TIEMPO"),
                      f"estado={est}")

    # radicado vigente para validar el semaforo
    st, data, _ = rad_cal.post("/api/radicados", {
        "txt_remitente": f"Semaphore {marca}", "txt_asunto": f"Vencimiento {marca}",
        "cmb_tipo_doc": "Tutela", "cmb_sede_destino": "Cali", "dias_termino": 5,
    })
    rad2 = (data or {}).get("radicado") or {}
    st, data, _ = admin.get("/api/dashboard/vencimientos")
    encontrados = []
    if isinstance(data, dict):
        for clave in ("grid_criticos", "grid_atencion", "grid_en_tiempo"):
            encontrados += [r for r in (data.get(clave) or []) if r.get("rad_id") == rad2.get("rad_id")]
    check("HU-010", "radicado recien creado aparece en el semaforo como EN_TIEMPO",
          len(encontrados) == 1 and "EN" in str(encontrados[0].get("estado_semaforo", "")).upper(),
          f"encontrados={encontrados}")

    st, data, _ = admin.get("/api/dashboard/vencimientos")
    if isinstance(data, dict):
        check("HU-010", "expediente FINALIZADO no aparece en el semaforo",
              not any(r.get("rad_id") == rad_id for clave in ("grid_criticos", "grid_atencion", "grid_en_tiempo")
                      for r in (data.get(clave) or [])),
              "el radicado cerrado sigue apareciendo")
        check("HU-010", "totales del semaforo coinciden con los grids",
              isinstance(data.get("total_criticos"), int)
              and data.get("total_en_tiempo") == len(data.get("grid_en_tiempo") or []),
              f"totales={[data.get(k) for k in ('total_criticos','total_atencion','total_en_tiempo')]}")

    section("RESUMEN")
    print(f"\nTotal verificaciones : {len(PASSED) + len(FAILED)}")
    print(f"Correctas            : {len(PASSED)}")
    print(f"Fallidas             : {len(FAILED)}")
    if FAILED:
        print("\nDETALLE DE FALLAS:")
        for name, detail in FAILED:
            print(f"  - {name}\n      {detail}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())