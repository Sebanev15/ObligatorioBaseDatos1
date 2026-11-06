"""Reglas compartidas por partido, planilla, goles y tarjetas."""
from datetime import datetime, time, timedelta

from fastapi import HTTPException, status

from ..db import fetch_one


def partido(conn, id_partido: int) -> dict | None:
    fila = fetch_one(
        conn,
        """SELECT p.*, t.hora_inicio, t.hora_fin
           FROM partido p JOIN turno t ON t.id_turno = p.id_turno
           WHERE p.id_partido = %s""",
        (id_partido,),
    )
    if fila is None:
        return None
    for campo in ("hora_inicio", "hora_fin"):
        valor = fila[campo]
        if isinstance(valor, timedelta):
            segundos = int(valor.total_seconds()) % (24 * 60 * 60)
            fila[campo] = time(
                segundos // 3600,
                (segundos % 3600) // 60,
                segundos % 60,
                valor.microseconds,
            )
        elif isinstance(valor, str):
            fila[campo] = time.fromisoformat(valor)
    return fila


def exigir_partido_editable(conn, id_partido: int) -> dict:
    fila = partido(conn, id_partido)
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Partido no encontrado")
    if fila["estado"] in ("cancelado", "postergado"):
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede registrar información en un partido cancelado o postergado")
    fin = datetime.combine(fila["dia"], fila["hora_fin"])
    if fila["estado"] == "jugado" and datetime.now() > fin + timedelta(hours=48):
        raise HTTPException(status.HTTP_409_CONFLICT, "La planilla y el resultado solo se pueden corregir hasta 48 horas después")
    return fila


def exigir_horario_pasado(fila: dict) -> None:
    if datetime.now() < datetime.combine(fila["dia"], fila["hora_fin"]):
        raise HTTPException(status.HTTP_409_CONFLICT, "El partido solo puede marcarse como jugado después de que termine su turno")
