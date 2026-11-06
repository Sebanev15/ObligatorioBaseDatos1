import unittest
from datetime import date, time, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.deps import CurrentUser, _solo_admin
from app.routers import _partidos
from app.routers import partidos
from app.routers.partidos import router
from app.schemas.partido import PartidoPatch


class MatchAuthorizationTests(unittest.TestCase):
    def test_planillero_cannot_change_match_status(self):
        route = next(
            route
            for route in router.routes
            if route.path == "/partidos/{id_partido}/estado" and "PATCH" in route.methods
        )
        self.assertIn(_solo_admin, [dependency.call for dependency in route.dependant.dependencies])

        with self.assertRaises(HTTPException) as error:
            _solo_admin(CurrentUser(correo="planillero@example.com", rol="planillero"))

        self.assertEqual(error.exception.status_code, 403)

    def test_mysql_time_durations_are_normalized_before_edit_rules(self):
        row = {
            "id_partido": 1,
            "dia": date(2026, 11, 5),
            "hora_inicio": timedelta(hours=18),
            "hora_fin": timedelta(hours=19),
            "estado": "programado",
        }
        with patch.object(_partidos, "fetch_one", return_value=row):
            result = _partidos.partido(object(), 1)
            editable = _partidos.exigir_partido_editable(object(), 1)

        self.assertEqual(result["hora_inicio"], time(18))
        self.assertEqual(result["hora_fin"], time(19))
        self.assertEqual(editable["hora_fin"], time(19))

    def test_played_match_reports_correction_window_instead_of_server_error(self):
        row = {
            "id_partido": 1,
            "dia": date(2026, 9, 26),
            "hora_inicio": time(18),
            "hora_fin": time(19),
            "estado": "jugado",
        }
        with patch.object(_partidos, "partido", return_value=row):
            with self.assertRaises(HTTPException) as error:
                _partidos.exigir_partido_editable(object(), 1)

        self.assertEqual(error.exception.status_code, 409)
        self.assertIn("48 horas", error.exception.detail)

    def test_marking_match_played_recalculates_sanctions_for_carded_players(self):
        connection = object()
        match = {"id_partido": 4, "id_torneo": 9, "estado": "programado"}
        with patch.object(partidos, "get_connection") as get_connection, patch.object(
            partidos, "buscar_partido", return_value=match
        ), patch.object(
            partidos, "exigir_horario_pasado"
        ), patch.object(
            partidos, "execute"
        ), patch.object(
            partidos, "fetch_all", return_value=[{"ci_jugador": 1234567}, {"ci_jugador": 7654321}]
        ), patch.object(
            partidos, "recalcular_sanciones_automaticas"
        ) as recalculate, patch.object(
            partidos, "_obtener", return_value=match
        ):
            get_connection.return_value.__enter__.return_value = connection

            partidos.cambiar_estado(
                4,
                PartidoPatch.model_validate({"estado": "jugado"}),
                SimpleNamespace(rol="administrador"),
            )

        self.assertEqual(
            recalculate.call_args_list,
            [
                unittest.mock.call(connection, 9, 1234567),
                unittest.mock.call(connection, 9, 7654321),
            ],
        )


if __name__ == "__main__":
    unittest.main()
