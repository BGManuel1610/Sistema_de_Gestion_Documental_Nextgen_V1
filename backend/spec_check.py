"""Verifica el cumplimiento literal de los criterios de aceptacion del README.

Cada check cita la linea del README vigente. El README fue corregido para
alinearse con la Propuesta Comercial V1.1 (fuente de verdad contractual), de modo
que las expectativas de este verificador reflejan el documento ya armonizado.
"""
import json, sys, os, urllib.request, urllib.error, uuid

# Permite ejecutar el script desde cualquier directorio de trabajo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = os.getenv("BASE_URL", "http://localhost:8000")
PWD = "Password123!"
ok = fail = 0
rows = []


def check(hu, criterio, cumple, detalle):
    global ok, fail
    if cumple:
        ok += 1
    else:
        fail += 1
    rows.append((("OK " if cumple else "NO "), hu, criterio, detalle))


def req(method, path, token=None, body=None, raw=None, ctype=None):
    h = {}
    d = None
    if token:
        h["Authorization"] = "Bearer " + token
    if raw is not None:
        d = raw
        if ctype:
            h["Content-Type"] = ctype
    elif body is not None:
        d = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=d, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=40) as resp:
            t = resp.read()
            try:
                return resp.status, json.loads(t)
            except Exception:
                return resp.status, t
    except urllib.error.HTTPError as e:
        t = e.read()
        try:
            return e.code, json.loads(t)
        except Exception:
            return e.code, t
    except Exception as e:
        return 0, {"error": str(e)}


def login(email, sede):
    st, d = req("POST", "/api/auth/login",
                body={"user_email": email, "user_password": PWD, "sede": sede})
    return d.get("access_token")


def radicado(token, marca, destino="Bogotá"):
    st, d = req("POST", "/api/radicados", token,
                body={"txt_remitente": f"Spec {marca}", "txt_asunto": f"Spec {marca}",
                      "cmb_tipo_doc": "Oficio", "cmb_sede_destino": destino})
    return (d or {}).get("radicado") or {}


admin = login("admin@docusol.com", "Bogotá")
rad_bog = login("radicador.bogota@docusol.com", "Bogotá")
ges_bog = login("gestionador.bogota@docusol.com", "Bogotá")
ges_cal = login("gestionador.cali@docusol.com", "Cali")
marca = uuid.uuid4().hex[:6]

# ---------------------------------------------------------------- HU-003
# README:184 termino legal de 5 dias habiles con exclusion de festivos (Ley Emiliani).
# Se recalcula el plazo aqui de forma independiente y se compara con la app, de modo
# que el check no dependa de la propia implementacion que intenta validar.
from datetime import datetime, timedelta
import holidays
from app.utils.business_days import sumar_dias_habiles_colombianos


def dias_habiles_emiliani(base, dias):
    """Referencia independiente: fines de semana, festivos y Emiliani (dom->lun)."""
    cache = {}

    def habil(f):
        if f.weekday() >= 5:
            return False
        if f.year not in cache:
            hs = holidays.country_holidays("CO", years=[f.year])
            movidos = set()
            for h in hs:
                movidos.add(h + timedelta(days=1) if h.weekday() == 6 else h)
            cache[f.year] = movidos
        return f.date() not in cache[f.year]

    actual, cont = base, 0
    while cont < dias:
        actual += timedelta(days=1)
        if habil(actual):
            cont += 1
    return actual


emiliani_ok = True
casos = 0
emiliani_fallos = []

# Se barre una ventana de 5 anos desde varias fechas base, lo que cubre con
# seguridad los festivos que caen en domingo dentro del rango.
for anio in (2026, 2027, 2028, 2029, 2030):
    for mes in range(1, 13):
        for dia in (1, 11, 21):
            try:
                base = datetime(anio, mes, dia, 8, 0)
            except ValueError:
                continue
            for plazo in (3, 5, 10):
                casos += 1
                esperado = dias_habiles_emiliani(base, plazo)
                obtenido = sumar_dias_habiles_colombianos(base, plazo)
                if obtenido.date() != esperado.date():
                    emiliani_ok = False
                    if len(emiliani_fallos) < 4:
                        emiliani_fallos.append(
                            f"base {base.date()} plazo {plazo}: app={obtenido.date()} "
                            f"ref={esperado.date()}")

# Comprobacion explicita de la regla: si un festivo cae en domingo, se traslada
# al lunes siguiente y ESE lunes no debe descontarse del plazo. Se arranca en el
# propio domingo: si el lunes se contara, el plazo caeria en el lunes; como se
# excluye, cae en el martes siguiente. La funcion nunca cuenta el dia inicial.
dom_shift_ok = True
dom_detalle = "sin ningun festivo en domingo entre 2026 y 2035"
for anio in range(2026, 2036):
    encontrado = None
    for fest in holidays.country_holidays("CO", years=[anio]):
        if fest.weekday() == 6:
            encontrado = fest
            break
    if not encontrado:
        continue
    base = datetime(encontrado.year, encontrado.month, encontrado.day, 8, 0)
    obtenido = sumar_dias_habiles_colombianos(base, 1).date()
    # El lunes siguiente esta trasladado por Emiliani, luego no se cuenta.
    esperado = base.date() + timedelta(days=2)
    dom_detalle = (f"festivo {encontrado} cae en domingo; arrancando ese dia, "
                   f"+1 dia habil da {obtenido} (esperado {esperado}: el lunes "
                   f"trasladado no se descuenta)")
    dom_shift_ok = obtenido == esperado
    break

check("HU-003", "README:184 '5 dias habiles ... Ley Emiliani' (plazo recalculado de forma independiente)",
      emiliani_ok,
      f"{casos} plazos contrastados contra una referencia propia"
      + ("" if emiliani_ok else "; fallos: " + " | ".join(emiliani_fallos)))

check("HU-003", "README:184 el festivo que cae en domingo NO se cuenta el lunes",
      dom_shift_ok, dom_detalle)

# README:183 y 185: se registra la sede de destino y el expediente se enruta a ella
r1 = radicado(rad_bog, marca + "-sede", destino="Medellín")
check("HU-003", "README:183 'Registro ... y sede de destino'",
      r1.get("rad_sede_destino") == "Medellín",
      f"cmb_sede_destino=Medellin queda en rad_sede_destino={r1.get('rad_sede_destino')!r}")

check("HU-003", "README:185 enrutamiento inicial a la sede destino, estado TRASLADADO",
      r1.get("rad_sede_actual") == "Medellín" and r1.get("rad_estado") == "TRASLADADO",
      f"radicado en Bogota con destino Medellin -> rad_sede_actual="
      f"{r1.get('rad_sede_actual')!r}, rad_estado={r1.get('rad_estado')!r}")

# ---------------------------------------------------------------- HU-005
# README:26 (matriz corregida) HU-005 = Radicador, Gestionador, Administrador.
# Se parte de un radicado en la sede del Gestionador (destino = Bogota) para que
# el 403 no se dispare por la sede sino por el rol, que es lo que se evalua.
r_h5 = radicado(rad_bog, marca + "-h5", destino="Bogotá")
st, _ = req("POST", "/api/traslados", ges_bog,
            body={"rad_id": r_h5.get("rad_id"), "cmb_nueva_sede": "Cali",
                  "txt_motivo_traslado": "Spec HU-005 gestionador"})
check("HU-005", "README:26 HU-005 'Radicador, Gestionador, Administrador'",
      st in (200, 201), f"el Gestionador de Bogota traslada un radicado de Bogota -> HTTP {st}")

# ---------------------------------------------------------------- HU-002
# README:147 correo obligatorio @docusol.com
st, d = req("POST", "/api/usuarios", admin,
            body={"txt_nombre": "Dominio externo", "txt_email": f"hacker{marca}@otraempresa.com",
                  "cmb_rol": "Radicador", "cmb_sede": "Bogotá", "usr_password": "Temporal123!"})
check("HU-002", "README:147 'asignacion obligatoria de correo @docusol.com'",
      st == 400, f"correo externo @otraempresa.com -> HTTP {st} "
                 f"({(d or {}).get('detail')})")

# y un correo valido si debe aceptarse
st, d = req("POST", "/api/usuarios", admin,
            body={"txt_nombre": "Dominio interno", "txt_email": f"valido{marca}@docusol.com",
                  "cmb_rol": "Radicador", "cmb_sede": "Bogotá", "usr_password": "Temporal123!"})
check("HU-002", "README:147 el correo @docusol.com valido si se acepta",
      st in (200, 201), f"correo interno @docusol.com -> HTTP {st}")

# ---------------------------------------------------------------- HU-006
# README:226 bandeja = pendientes de la propia sede (TRASLADADO de otra sede + RADICADO local)
r2 = radicado(rad_bog, marca + "-bandeja")
st, pend = req("GET", "/api/recepcion/pendientes", ges_bog)
estados = {r["rad_id"]: r["rad_estado"] for r in (pend or [])} if isinstance(pend, list) else {}
check("HU-006", "README:226 bandeja con los pendientes de la sede (incluye RADICADO local)",
      estados.get(r2.get("rad_id")) == "RADICADO",
      f"el radicado RADICADO (id={r2.get('rad_id')}) aparece en la bandeja con "
      f"estado={estados.get(r2.get('rad_id'))!r}")

# README:227 bloqueo al aceptar desde otra sede, respondido con 404
st, resp = req("POST", f"/api/recepcion/aceptar/{r2.get('rad_id')}", ges_cal)
check("HU-006", "README:227 'Bloqueo ... 404' si un usuario de otra sede acepta",
      st == 404, f"el Gestionador de Cali acepta un radicado de Bogota y recibe HTTP {st}")

# ---------------------------------------------------------------- HU-007
# README:244 el Administrador puede finalizar expedientes de cualquier sede
admin_cal = login("admin.cali@docusol.com", "Cali")
r3 = radicado(rad_bog, marca + "-cierre")
# Se acepta para poder cerrar.
req("POST", f"/api/recepcion/aceptar/{r3.get('rad_id')}", ges_bog)
boundary = "--b" + uuid.uuid4().hex
pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"rad_id\"\r\n\r\n{r3.get('rad_id')}\r\n"
           f"--{boundary}\r\nContent-Disposition: form-data; name=\"txt_observacion_cierre\"\r\n\r\nspec\r\n"
           f"--{boundary}\r\nContent-Disposition: form-data; name=\"file_respuesta\"; filename=\"r.pdf\"\r\n"
           f"Content-Type: application/pdf\r\n\r\n").encode() + pdf + f"\r\n--{boundary}--\r\n".encode()
st, resp = req("POST", "/api/cierre", admin_cal, raw=payload,
               ctype=f"multipart/form-data; boundary={boundary}")
check("HU-007", "README:244 el Administrador puede finalizar de cualquier sede",
      st in (200, 201), f"el Administrador de Cali cierra un radicado de Bogota -> HTTP {st}")

# ---------------------------------------------------------------- HU-008
# README:31 (matriz corregida) HU-008 = solo Administrador
st, _ = req("GET", "/api/auditoria/trazabilidad/X", ges_bog)
check("HU-008", "README:31 HU-008 'Administrador' ( supervision de auditoria)",
      st == 403, f"el Gestionador consulta la auditoria y recibe HTTP {st}")

st, _ = req("GET", f"/api/auditoria/trazabilidad/{r2.get('rad_codigo')}", admin)
check("HU-008", "README:31 el Administrador si accede a la auditoria",
      st == 200, f"el Administrador consulta la auditoria y recibe HTTP {st}")

# ---------------------------------------------------------------- HU-010
# README:33 (matriz corregida) HU-010 = Administrador, Gestionador
st, _ = req("GET", "/api/dashboard/vencimientos", rad_bog)
check("HU-010", "README:33 HU-010 'Administrador, Gestionador' (Radicador excluido)",
      st == 403, f"el Radicador consulta el dashboard y recibe HTTP {st}")

st, _ = req("GET", "/api/dashboard/vencimientos", ges_bog)
check("HU-010", "README:33 el Gestionador si accede al dashboard",
      st == 200, f"el Gestionador consulta el dashboard y recibe HTTP {st}")

# ---------------------------------------------------------------- informe
print("=" * 78)
print("CONFORMIDAD CON EL README VIGENTE (matriz de roles armonizada con la "
      "Propuesta Comercial V1.1)")
print("=" * 78)
for flag, hu, criterio, detalle in rows:
    print(f"[{flag}] {hu}")
    print(f"       {criterio}")
    print(f"       -> {detalle}\n")
print("=" * 78)
print(f"Cumple: {ok} | No cumple: {fail} | Total: {ok + fail}")
print("=" * 78)