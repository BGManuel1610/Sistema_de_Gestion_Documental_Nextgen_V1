from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from ..database.session import get_db
from ..models.radicado import Radicado
from ..models.anexo import Anexo
from ..models.historial_traslado import HistorialTraslado
from ..models.historial_aceptacion import HistorialAceptacion
from ..models.historial_cierre import HistorialCierre
from ..models.respuesta import Respuesta
from ..models.usuario import Usuario
from ..schemas.auditoria import TrazabilidadResponse, TrazabilidadItem
from ..security.jwt_handler import get_current_user
from ..security.access_control import exigir_roles

router = APIRouter(prefix="/api/auditoria", tags=["auditoria"])

@router.get("/trazabilidad/{rad_codigo}", response_model=TrazabilidadResponse)
def consultar_trazabilidad(
    rad_codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-008: Consulta de Trazabilidad e Historial Inalterable.
    C.A.1: Búsqueda por código de expediente txt_buscar_radicado.
    C.A.2: Consulta uniendo tbl_radicados, tbl_historial_traslados y tbl_usuarios.
    C.A.3: Si no existe, alerta amarilla exacta.
    C.A.4: Renderizar cronológicamente grid_linea_tiempo:
           Fecha/Hora, Usuario, Sede Origen, Sede Destino, Acción Realizada, Estado.
    C.A.5: Solo lectura estricto.
    """
    exigir_roles(current_user, "Administrador")
    codigo_limpio = rad_codigo.strip()
    radicado = (
        db.query(Radicado)
        .filter(Radicado.rad_codigo == codigo_limpio)
        .first()
    )
    
    # C.A.3: Validación de existencia con mensaje exacto
    if not radicado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El número de radicado ingresado no existe en el sistema."
        )

    # Mapa unico de usuarios: evita una consulta por evento (el timeline antes
    # hacia un SELECT a tbl_usuarios dentro de cada iteracion).
    usuarios = {u.usr_id: u for u in db.query(Usuario).all()}

    def nombre_usuario(usr_id, por_defecto):
        usr = usuarios.get(usr_id)
        return usr.usr_nombre if usr else por_defecto

    traslados = (
        db.query(HistorialTraslado)
        .filter(HistorialTraslado.tra_rad_id == radicado.rad_id)
        .order_by(HistorialTraslado.tra_fecha_hora.asc())
        .all()
    )
    aceptaciones = (
        db.query(HistorialAceptacion)
        .filter(HistorialAceptacion.acep_rad_id == radicado.rad_id)
        .order_by(HistorialAceptacion.acep_fecha_hora.asc())
        .all()
    )

    # Construir línea de tiempo cronológica
    linea_tiempo: List[dict] = []

    usuario_creador = usuarios.get(radicado.rad_usuario_radicador)

    # 1. Evento de creación
    linea_tiempo.append({
        "fecha_hora_dt": radicado.rad_fecha_creacion,
        "fecha_hora": str(radicado.rad_fecha_creacion)[:19],
        "usuario": usuario_creador.usr_nombre if usuario_creador else "Sistema",
        "sede_origen": usuario_creador.usr_sede if usuario_creador else radicado.rad_sede_actual,
        "sede_destino": radicado.rad_sede_destino,
        "accion_realizada": f"Radicación inicial ({radicado.rad_tipo_doc}) - {radicado.rad_asunto}",
        "estado": "RADICADO"
    })

    # 2. Eventos de carga de anexos (HU-008: la digitalizacion es parte de la traza)
    anexos = (
        db.query(Anexo)
        .filter(Anexo.anx_rad_id == radicado.rad_id)
        .order_by(Anexo.anx_fecha_carga.asc(), Anexo.anx_id.asc())
        .all()
    )
    for anexo in anexos:
        linea_tiempo.append({
            "fecha_hora_dt": anexo.anx_fecha_carga,
            "fecha_hora": str(anexo.anx_fecha_carga)[:19],
            "usuario": nombre_usuario(anexo.anx_usuario_id, "Usuario no registrado"),
            "sede_origen": radicado.rad_sede_actual,
            "sede_destino": radicado.rad_sede_actual,
            "accion_realizada": f"Carga de anexo digitalizado: {anexo.anx_nombre_original}",
            "estado": "RADICADO"
        })

    # 3. Eventos de traslados
    for tra in traslados:
        linea_tiempo.append({
            "fecha_hora_dt": tra.tra_fecha_hora,
            "fecha_hora": str(tra.tra_fecha_hora)[:19],
            "usuario": nombre_usuario(tra.tra_usuario_id, "Usuario Desconocido"),
            "sede_origen": tra.tra_sede_origen,
            "sede_destino": tra.tra_sede_destino,
            "accion_realizada": f"Traslado inter-sede. Motivo: {tra.tra_motivo}",
            "estado": "TRASLADADO",
            "ip_origen": tra.tra_ip_origen
        })

    # 4. Eventos de aceptación con su hora y usuario registrados
    for aceptacion in aceptaciones:
        linea_tiempo.append({
            "fecha_hora_dt": aceptacion.acep_fecha_hora,
            "fecha_hora": str(aceptacion.acep_fecha_hora)[:19],
            "usuario": nombre_usuario(aceptacion.acep_usuario_id, "Gestionador"),
            "sede_origen": aceptacion.acep_sede,
            "sede_destino": aceptacion.acep_sede,
            "accion_realizada": "Aceptación formal de expediente en bandeja de gestión",
            "estado": "ACEPTADO",
            "ip_origen": aceptacion.acep_ip_origen
        })

    # 4. Cierres con el usuario que ejecutó la acción
    respuestas = db.query(Respuesta).filter(Respuesta.res_rad_id == radicado.rad_id).all()
    cierres = (
        db.query(HistorialCierre)
        .filter(HistorialCierre.cierre_rad_id == radicado.rad_id)
        .order_by(HistorialCierre.cierre_fecha_hora.asc())
        .all()
    )
    cierres_por_radicado = {cierre.cierre_rad_id: cierre for cierre in cierres}
    respuestas_por_radicado = {respuesta.res_rad_id: respuesta for respuesta in respuestas}

    for cierre in cierres:
        resp = respuestas_por_radicado.get(cierre.cierre_rad_id)
        linea_tiempo.append({
            "fecha_hora_dt": cierre.cierre_fecha_hora,
            "fecha_hora": str(cierre.cierre_fecha_hora)[:19],
            "usuario": nombre_usuario(cierre.cierre_usuario_id, "Usuario desconocido"),
            "sede_origen": cierre.cierre_sede,
            "sede_destino": cierre.cierre_sede,
            "accion_realizada": (
                f"Cierre de trámite con respuesta en PDF: {resp.res_observacion}"
                if resp else "Cierre de trámite"
            ),
            "estado": "FINALIZADO",
            "ip_origen": cierre.cierre_ip_origen
        })

    for resp in respuestas:
        if resp.res_rad_id in cierres_por_radicado:
            continue
        linea_tiempo.append({
            "fecha_hora_dt": resp.res_fecha_cierre,
            "fecha_hora": str(resp.res_fecha_cierre)[:19],
            "usuario": "Usuario de cierre anterior no registrado",
            "sede_origen": radicado.rad_sede_actual,
            "sede_destino": radicado.rad_sede_actual,
            "accion_realizada": f"Cierre de trámite con respuesta en PDF: {resp.res_observacion}",
            "estado": "FINALIZADO"
        })

    # Ordenar cronológicamente. Un registro con fecha nula se ordena al final en
    # lugar de romper el sort con datetime vs None (HTTP 500).
    linea_tiempo.sort(key=lambda x: (x["fecha_hora_dt"] is None, x["fecha_hora_dt"] or datetime.min))

    # Remover auxiliar de fecha y convertir al esquema
    items = [
        TrazabilidadItem(
            fecha_hora=e["fecha_hora"],
            usuario=e["usuario"],
            sede_origen=e["sede_origen"],
            sede_destino=e["sede_destino"],
            accion_realizada=e["accion_realizada"],
            estado=e["estado"],
            ip_origen=e.get("ip_origen")
        )
        for e in linea_tiempo
    ]

    return TrazabilidadResponse(
        rad_codigo=radicado.rad_codigo,
        rad_asunto=radicado.rad_asunto,
        rad_estado_actual=radicado.rad_estado,
        linea_tiempo=items
    )


# Alias de compatibilidad con la ruta documentada en el README (README:232).
@router.get("/{rad_codigo}", response_model=TrazabilidadResponse, include_in_schema=False)
def consultar_trazabilidad_alias(
    rad_codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """README:232 declara GET /api/auditoria/{codigo_radicado}; delega en la canonica."""
    return consultar_trazabilidad(rad_codigo, db, current_user)
