import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.routers import equipos
from app.schemas.equipo import EquipoPatch


class TeamEditTests(unittest.TestCase):
    def test_patch_accepts_tournament_and_faculty_fields(self):
        data = EquipoPatch.model_validate({"id_torneo": 8, "id_facultad": 3})

        self.assertEqual(data.id_torneo, 8)
        self.assertEqual(data.id_facultad, 3)

    def test_tournament_change_moves_roster_and_preserves_captain(self):
        connection = object()
        team = {
            "id_equipo": 4,
            "nombre": "Equipo",
            "id_torneo": 2,
            "id_facultad": 3,
            "ci_capitan": 1234567,
        }
        statements = []
        with patch.object(equipos, "get_connection") as get_connection, patch.object(
            equipos, "_equipo_bloqueado", return_value=team
        ), patch.object(
            equipos, "_exigir_inscripcion"
        ) as require_registration, patch.object(
            equipos,
            "fetch_all",
            return_value=[{"ci_jugador": 1234567, "numero_camiseta": 10, "id_facultad": 3}],
        ), patch.object(
            equipos, "fetch_one", return_value=None
        ), patch.object(
            equipos,
            "execute",
            side_effect=lambda conn, sql, params=(): statements.append((sql, params)),
        ), patch.object(
            equipos, "_obtener", return_value={"id_equipo": 4, "id_torneo": 8}
        ):
            get_connection.return_value.__enter__.return_value = connection
            result = equipos.modificar(
                4,
                EquipoPatch.model_validate({"id_torneo": 8}),
                SimpleNamespace(rol="administrador"),
            )

        self.assertEqual(result["id_torneo"], 8)
        require_registration.assert_any_call(connection, 2)
        require_registration.assert_any_call(connection, 8)
        sql = [statement for statement, _ in statements]
        self.assertIn("DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s", sql)
        self.assertTrue(any(statement.startswith("INSERT INTO equipo_jugador_torneo") for statement in sql))
        self.assertEqual(statements[-1][1], (1234567, 4))

    def test_tournament_change_is_rejected_when_team_has_matches(self):
        team = {
            "id_equipo": 4,
            "nombre": "Equipo",
            "id_torneo": 2,
            "id_facultad": 3,
            "ci_capitan": None,
        }
        with patch.object(equipos, "get_connection") as get_connection, patch.object(
            equipos, "_equipo_bloqueado", return_value=team
        ), patch.object(
            equipos, "_exigir_inscripcion"
        ), patch.object(
            equipos, "fetch_all", return_value=[]
        ), patch.object(
            equipos, "fetch_one", return_value={"id_partido": 11}
        ), patch.object(
            equipos, "execute"
        ) as execute:
            get_connection.return_value.__enter__.return_value = object()
            with self.assertRaises(HTTPException) as error:
                equipos.modificar(
                    4,
                    EquipoPatch.model_validate({"id_torneo": 8}),
                    SimpleNamespace(rol="administrador"),
                )

        self.assertEqual(error.exception.status_code, 409)
        self.assertIn("partidos", error.exception.detail)
        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
