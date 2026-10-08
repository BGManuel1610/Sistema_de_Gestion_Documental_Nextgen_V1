from fastapi import HTTPException, status

from ..models.usuario import Usuario


def exigir_roles(usuario: Usuario, *roles: str) -> None:
    if usuario.usr_rol not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta acción."
        )


def exigir_misma_sede(usuario: Usuario, sede: str) -> None:
    exigir_sede(usuario.usr_sede, sede)


def exigir_sede(sede_usuario: str, sede: str) -> None:
    if sede_usuario != sede:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solo puede operar sobre la sede {sede_usuario}."
        )