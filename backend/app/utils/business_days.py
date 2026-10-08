"""
Calculo de dias habiles calendario colombiano.

Ademas de excluir fines de semana y festivos, aplica la Ley Emiliani
(Ley 51 de 1983, art. 2 y ss.): los festivos que caen en domingo se trasladan
al lunes siguiente. Omitir ese traslado hace que el plazo legal se corra uno o
dos dias, con el consiguiente riesgo de caducidad del termino.

El README exige "5 dias habiles" y el computo debe ser el vigente en Colombia.
"""
from datetime import datetime, timedelta
from functools import lru_cache

import holidays


@lru_cache(maxsize=16)
def _festivos(anios: tuple) -> holidays.HolidayBase:
    """Calendario de festivos Colombia cacheado por rango de anios."""
    return holidays.country_holidays("CO", years=list(anios))


@lru_cache(maxsize=512)
def _festivos_trasladados(anio: int) -> frozenset:
    """
    Festivos del año aplicando la Ley Emiliani: los que caen en domingo se
    mueven al lunes siguiente, de modo que ese lunes no se descuenta del plazo.
    """
    base = holidays.country_holidays("CO", years=[anio])
    resultado = set()
    for fecha in base:
        movido = fecha
        # Solo los festivos que caen en domingo pasan al lunes.
        if fecha.weekday() == 6:
            movido = fecha + timedelta(days=1)
        resultado.add(movido)
    return frozenset(resultado)


def _es_dia_habil(fecha: datetime, cache_anios: dict) -> bool:
    if fecha.weekday() >= 5:
        return False
    anio = fecha.year
    if anio not in cache_anios:
        cache_anios[anio] = _festivos_trasladados(anio)
    return fecha.date() not in cache_anios[anio]


def sumar_dias_habiles_colombianos(fecha_inicio: datetime, dias: int) -> datetime:
    """
    Devuelve la fecha en que se cumple el plazo de `dias` dias habiles, sin
    contar el dia de radicacion. Los dias habiles excluyen fines de semana,
    festivos ordinarios y festivos trasladados por la Ley Emiliani.
    """
    if dias <= 0:
        return fecha_inicio

    cache_anios: dict = {}
    fecha_limite = fecha_inicio
    dias_sumados = 0

    # Tope de seguridad: evita un bucle infinito si el calendario se agota.
    # Un ano de dias habiles es ~261; el margen absorbe cambios de calendario.
    max_iteraciones = (dias * 3) + 60

    for _ in range(max_iteraciones):
        if dias_sumados >= dias:
            break
        fecha_limite += timedelta(days=1)
        if _es_dia_habil(fecha_limite, cache_anios):
            dias_sumados += 1

    return fecha_limite


def contar_dias_habiles(fecha_inicio: datetime, fecha_fin: datetime) -> int:
    """Dias habiles transcurridos entre dos fechas (ambos inclusive el inicio)."""
    if fecha_fin <= fecha_inicio:
        return 0
    cache_anios: dict = {}
    total = 0
    actual = fecha_inicio
    while actual < fecha_fin:
        if _es_dia_habil(actual, cache_anios):
            total += 1
        actual += timedelta(days=1)
    return total