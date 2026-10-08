from datetime import date, datetime, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.radicado import Radicado
from ..models.usuario import Usuario
from ..schemas.reporte import ReporteItem
from ..security.jwt_handler import get_current_user, get_current_user_with_query_token
from ..security.access_control import exigir_roles
from ..utils.excel_generator import generate_radicados_excel

router = APIRouter(prefix="/api/reportes", tags=["reportes"])

def _filtrar_radicados(
    db: Session,
    dtp_fecha_inicio: Optional[date],
    dtp_fecha_fin: Optional[date],
    cmb_filtro_sede: Optional[str],
    cmb_filtro_estado: Optional[str],
    current_user: Optional[Usuario] = None
) -> List[Radicado]:
    # C.A.2: Si fecha_final < fecha_inicial, detener con mensaje exacto
    if dtp_fecha_inicio and dtp_fecha_fin:
        if dtp_fecha_fin < dtp_fecha_inicio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rango de fechas incoherente. La fecha final no puede ser anterior a la inicial."
            )

    query = db.query(Radicado)

    # Propuesta Comercial (Perfil Gestionador): el gestor tambien genera reportes.
    # El aislamiento por sede se aplica en el servidor e ignora cualquier sede
    # solicitada, de modo que un gestionador nunca vea datos de otra sede.
    if current_user is not None and current_user.usr_rol != "Administrador":
        query = query.filter(Radicado.rad_sede_actual == current_user.usr_sede)
    elif cmb_filtro_sede and cmb_filtro_sede != "Todas":
        query = query.filter(Radicado.rad_sede_actual == cmb_filtro_sede)

    if dtp_fecha_inicio:
        dt_inicio = datetime.combine(dtp_fecha_inicio, time.min)
        query = query.filter(Radicado.rad_fecha_creacion >= dt_inicio)

    if dtp_fecha_fin:
        dt_fin = datetime.combine(dtp_fecha_fin, time.max)
        query = query.filter(Radicado.rad_fecha_creacion <= dt_fin)

    if cmb_filtro_sede and cmb_filtro_sede != "Todas" and (
        current_user is None or current_user.usr_rol == "Administrador"
    ):
        query = query.filter(Radicado.rad_sede_actual == cmb_filtro_sede)

    if cmb_filtro_estado and cmb_filtro_estado != "Todos":
        query = query.filter(Radicado.rad_estado == cmb_filtro_estado)

    return query.order_by(Radicado.rad_fecha_creacion.desc()).all()

@router.get("", response_model=List[ReporteItem])
def consultar_reporte(
    dtp_fecha_inicio: Optional[date] = None,
    dtp_fecha_fin: Optional[date] = None,
    cmb_filtro_sede: Optional[str] = "Todas",
    cmb_filtro_estado: Optional[str] = "Todos",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    HU-009: Generación de Reportes Parametrizados.
    C.A.1, C.A.2, C.A.3: Validación y consulta SQL sobre tbl_radicados.
    """
    exigir_roles(current_user, "Administrador", "Gestionador")
    radicados = _filtrar_radicados(
        db, dtp_fecha_inicio, dtp_fecha_fin, cmb_filtro_sede, cmb_filtro_estado, current_user
    )
    return radicados

# Alias de compatibilidad con la ruta documentada en el README.
# Se declara DESPUES de la ruta canonica para no capturarla.
@router.get("/parametrizados", response_model=List[ReporteItem], include_in_schema=False)
def consultar_reporte_alias(
    dtp_fecha_inicio: Optional[date] = None,
    dtp_fecha_fin: Optional[date] = None,
    cmb_filtro_sede: Optional[str] = "Todas",
    cmb_filtro_estado: Optional[str] = "Todos",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """README:245 declara GET /api/reportes/parametrizados; delega en la ruta canonica."""
    return consultar_reporte(
        dtp_fecha_inicio, dtp_fecha_fin, cmb_filtro_sede, cmb_filtro_estado, db, current_user
    )


@router.get("/exportar-excel")
def exportar_excel(
    dtp_fecha_inicio: Optional[date] = None,
    dtp_fecha_fin: Optional[date] = None,
    cmb_filtro_sede: Optional[str] = "Todas",
    cmb_filtro_estado: Optional[str] = "Todos",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user_with_query_token)
):
    """
    HU-009: C.A.4 & C.A.5:
    Generar y descargar archivo .xlsx estandarizado con la información filtrada.
    """
    exigir_roles(current_user, "Administrador", "Gestionador")
    radicados = _filtrar_radicados(
        db, dtp_fecha_inicio, dtp_fecha_fin, cmb_filtro_sede, cmb_filtro_estado, current_user
    )

    if not radicados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No existen registros para exportar."
        )

    datos = [
        {
            "rad_codigo": r.rad_codigo,
            "rad_remitente": r.rad_remitente,
            "rad_asunto": r.rad_asunto,
            "rad_tipo_doc": r.rad_tipo_doc,
            "rad_sede_destino": r.rad_sede_destino,
            "rad_sede_actual": r.rad_sede_actual,
            "rad_estado": r.rad_estado,
            "rad_fecha_creacion": r.rad_fecha_creacion,
            "rad_fecha_limite": r.rad_fecha_limite,
        }
        for r in radicados
    ]

    excel_io = generate_radicados_excel(datos)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_radicados_{timestamp}.xlsx"

    return Response(
        content=excel_io.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
