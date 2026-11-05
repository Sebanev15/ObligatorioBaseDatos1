import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.routers import _deletion


class DeletionTests(unittest.TestCase):
    def test_played_match_blocks_parent_cascade(self):
        with patch.object(_deletion, "fetch_all", return_value=[{"id_partido": 12}]), patch.object(
            _deletion, "execute"
        ) as execute:
            with self.assertRaises(HTTPException) as error:
                _deletion.eliminar_partidos_de_equipo(object(), 3)

        self.assertEqual(error.exception.status_code, 409)
        execute.assert_not_called()

    def test_unplayed_match_children_are_deleted_before_match(self):
        statements = []
        with patch.object(
            _deletion, "fetch_all", side_effect=[[], [{"id_partido": 12}]]
        ), patch.object(
            _deletion,
            "execute",
            side_effect=lambda conn, sql, params=(): statements.append(sql),
        ):
            _deletion.eliminar_partidos_de_equipo(object(), 3)

        self.assertEqual(
            [statement.split()[2] for statement in statements],
            ["gol", "tarjeta", "planilla_partido", "partido"],
        )

    def test_player_with_played_appearance_is_not_deleted(self):
        with patch.object(_deletion, "fetch_all", return_value=[{"id_partido": 12}]), patch.object(
            _deletion, "execute"
        ) as execute:
            with self.assertRaises(HTTPException) as error:
                _deletion.eliminar_jugador(object(), 1234567)

        self.assertEqual(error.exception.status_code, 409)
        execute.assert_not_called()

    def test_player_with_sanction_is_not_deleted(self):
        with patch.object(
            _deletion, "fetch_all", side_effect=[[], [{"id_sancion": 7}]]
        ), patch.object(_deletion, "execute") as execute:
            with self.assertRaises(HTTPException) as error:
                _deletion.eliminar_jugador(object(), 1234567)

        self.assertEqual(error.exception.status_code, 409)
        execute.assert_not_called()

    def test_roster_removal_preserves_played_participation(self):
        with patch.object(_deletion, "fetch_all", return_value=[{"id_partido": 12}]), patch.object(
            _deletion, "execute"
        ) as execute:
            with self.assertRaises(HTTPException) as error:
                _deletion.eliminar_participacion(object(), 3, 1234567)

        self.assertEqual(error.exception.status_code, 409)
        execute.assert_not_called()

    def test_roster_removal_preserves_sanction_attribution(self):
        with patch.object(
            _deletion, "fetch_all", side_effect=[[], [{"id_sancion": 7}]]
        ), patch.object(_deletion, "execute") as execute:
            with self.assertRaises(HTTPException) as error:
                _deletion.eliminar_participacion(object(), 3, 1234567)

        self.assertEqual(error.exception.status_code, 409)
        execute.assert_not_called()

    def test_team_with_sanctioned_roster_cannot_be_deleted(self):
        with patch.object(
            _deletion,
            "fetch_all",
            side_effect=[[], [], [{"id_sancion": 7}]],
        ), patch.object(_deletion, "execute") as execute:
            with self.assertRaises(HTTPException) as error:
                _deletion.eliminar_equipo(object(), 3)

        self.assertEqual(error.exception.status_code, 409)
        execute.assert_not_called()

    def test_unplayed_player_data_is_removed_before_player(self):
        statements = []
        with patch.object(_deletion, "fetch_all", return_value=[]), patch.object(
            _deletion,
            "execute",
            side_effect=lambda conn, sql, params=(): statements.append(sql),
        ):
            _deletion.eliminar_jugador(object(), 1234567)

        self.assertEqual(
            [statement.split()[:3] for statement in statements],
            [
                ["DELETE", "FROM", "gol"],
                ["DELETE", "FROM", "tarjeta"],
                ["DELETE", "FROM", "planilla_partido"],
                ["UPDATE", "equipo", "SET"],
                ["DELETE", "FROM", "equipo_jugador_torneo"],
                ["DELETE", "FROM", "jugador"],
            ],
        )
        self.assertIn("estado <> 'jugado'", statements[0])
        self.assertIn("estado <> 'jugado'", statements[1])
        self.assertIn("estado <> 'jugado'", statements[2])


if __name__ == "__main__":
    unittest.main()
