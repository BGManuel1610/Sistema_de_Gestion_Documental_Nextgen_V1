"""
Fuente unica de verdad para las sedes operativas del sistema.

Antes de este modulo la lista de sedes vivia duplicada en auth.py, usuarios.py,
schemas/auth.py, schemas/usuario.py, frontend/utils/sedes.js y docker-compose.yml,
lo que permitia que una divergencia rompiera en silencio HU-001 y HU-002.
"""
from typing import List

BOGOTA = "Bogotá"
MEDELLIN = "Medellín"
CALI = "Cali"

SEDES: List[str] = [BOGOTA, MEDELLIN, CALI]

SEDE_BOGOTA = BOGOTA
SEDE_MEDELLIN = MEDELLIN
SEDE_CALI = CALI

#: Slug usado en las URLs publicas de registro por sede (/crear-cuenta/{slug}).
SEDE_SLUGS = {
    "bogota": BOGOTA,
    "medellin": MEDELLIN,
    "cali": CALI,
}

ROLES = ["Administrador", "Radicador", "Gestionador"]

#: Sentinel que el frontend usa para "sin filtro de sede".
TODAS_LAS_SEDES = {"Todas", "TODAS", "todas", "All", "ALL", "all", "Todas las Sedes"}


def es_sede_valida(sede: str) -> bool:
    return sede in SEDES


def normalizar_sede(sede: str):
    """Devuelve la sede canonica o None si no es valida."""
    if not sede:
        return None
    return sede if sede in SEDES else None


def es_filtro_todas(sede: str) -> bool:
    return bool(sede) and sede in TODAS_LAS_SEDES


def sede_por_slug(slug: str):
    if not slug:
        return None
    return SEDE_SLUGS.get(str(slug).strip().lower())