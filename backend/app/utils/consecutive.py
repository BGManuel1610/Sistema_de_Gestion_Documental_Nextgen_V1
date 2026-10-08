from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.radicado import Radicado

def generate_radicado_code(db: Session) -> str:
    """
    Genera un código secuencial único con formato RAD-YYYY-XXXXX.
    Ejemplo: RAD-2026-00001.
    """
    current_year = datetime.now().year
    year_prefix = f"RAD-{current_year}-"
    
    # Buscar todos los radicados del año actual
    radicados = (
        db.query(Radicado.rad_codigo)
        .filter(Radicado.rad_codigo.like(f"{year_prefix}%"))
        .all()
    )
    
    max_consecutivo = 0
    for r in radicados:
        if r and r[0]:
            partes = r[0].split("-")
            if len(partes) >= 3 and partes[-1].isdigit():
                num = int(partes[-1])
                if num > max_consecutivo:
                    max_consecutivo = num
                    
    siguiente_consecutivo = max_consecutivo + 1
    codigo_generado = f"RAD-{current_year}-{siguiente_consecutivo:05d}"

    while db.query(Radicado.rad_id).filter(Radicado.rad_codigo == codigo_generado).first():
        siguiente_consecutivo += 1
        codigo_generado = f"RAD-{current_year}-{siguiente_consecutivo:05d}"

    return codigo_generado
