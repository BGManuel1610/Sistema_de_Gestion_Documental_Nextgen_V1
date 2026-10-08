from .auth import router as auth_router
from .usuarios import router as usuarios_router
from .radicados import router as radicados_router
from .anexos import router as anexos_router
from .traslados import router as traslados_router
from .recepcion import router as recepcion_router
from .cierre import router as cierre_router
from .auditoria import router as auditoria_router
from .reportes import router as reportes_router
from .dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "usuarios_router",
    "radicados_router",
    "anexos_router",
    "traslados_router",
    "recepcion_router",
    "cierre_router",
    "auditoria_router",
    "reportes_router",
    "dashboard_router",
]
