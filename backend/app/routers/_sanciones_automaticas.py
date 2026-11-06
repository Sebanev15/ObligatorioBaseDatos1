"""Recalcula las suspensiones automáticas derivadas de tarjetas de un jugador."""

from ..db import execute, fetch_all, fetch_one

_MOTIVOS_AUTOMATICOS = ("roja", "acumulacion de amarillas")


def recalcular_sanciones_automaticas(conn, id_torneo: int, ci_jugador: int) -> None:
    fetch_one(conn, "SELECT ci FROM jugador WHERE ci = %s FOR UPDATE", (ci_jugador,))
    tarjetas = fetch_all(
        conn,
        """SELECT ta.id_tarjeta, ta.color, ta.minuto, p.numero_fecha, p.dia
           FROM tarjeta ta
           JOIN partido p ON p.id_partido = ta.id_partido
           WHERE p.id_torneo = %s
             AND p.estado = 'jugado'
             AND ta.ci_jugador = %s
           ORDER BY p.dia, p.numero_fecha, ta.minuto, ta.id_tarjeta""",
        (id_torneo, ci_jugador),
    )

    execute(
        conn,
        """DELETE FROM sancion_jugador
           WHERE ci_jugador = %s AND id_torneo = %s
             AND motivo IN (%s, %s)""",
        (ci_jugador, id_torneo, *_MOTIVOS_AUTOMATICOS),
    )

    suspensiones: list[tuple[int, str]] = []
    amarillas = 0
    for tarjeta in tarjetas:
        if tarjeta["color"] == "roja":
            suspensiones.append((tarjeta["numero_fecha"] + 1, "roja"))
        elif tarjeta["color"] == "amarilla":
            amarillas += 1
            if amarillas % 3 == 0:
                suspensiones.append((tarjeta["numero_fecha"] + 1, "acumulacion de amarillas"))

    for fecha_inicio, motivo in suspensiones:
        execute(
            conn,
            """INSERT INTO sancion_jugador
               (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas)
               VALUES (%s, %s, %s, %s, 1)""",
            (ci_jugador, id_torneo, motivo, fecha_inicio),
        )
