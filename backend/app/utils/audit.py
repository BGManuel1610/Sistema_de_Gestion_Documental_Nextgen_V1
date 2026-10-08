"""Utilidades de auditoria transversales.

La Propuesta Comercial exige que la bitacora inalterable "especifique usuario,
fecha, hora, sede y direccion IP" (seccion "Impacto Estrategico"). Estos helpers
centralizan la obtencion de la IP del cliente para que los tres historiales
(traslado, aceptacion y cierre) la registren de forma consistente.
"""
from fastapi import Request


def obtener_ip(request: Request) -> str:
    """
    Devuelve la IP del cliente respetando la cadena de proxies.
    X-Forwarded-For es una cabecera controlada por el cliente, por lo que se toma
    solo el primer valor y el resto se ignoran. Si no hay proxy, se usa el
    socket real. Se limita a 45 chars (limite de VARCHAR para IPv6).
    """
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        real = request.headers.get("x-real-ip")
        ip = real.strip() if real else (request.client.host if request.client else None)
    return ip[:45] if ip else None