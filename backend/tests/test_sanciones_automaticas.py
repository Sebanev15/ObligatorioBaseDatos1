import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from app.routers import _sanciones_automaticas, tarjetas
from app.schemas.tarjeta import TarjetaCreate


class AutomaticSanctionTests(unittest.TestCase):
    def test_recalculation_creates_red_and_every_third_yellow_suspensions(self):
        cards = [
            {"id_tarjeta": 1, "color": "amarilla", "minuto": 5, "numero_fecha": 1, "dia": date(2026, 9, 1)},
            {"id_tarjeta": 2, "color": "amarilla", "minuto": 10, "numero_fecha": 2, "dia": date(2026, 9, 8)},
            {"id_tarjeta": 3, "color": "roja", "minuto": 20, "numero_fecha": 2, "dia": date(2026, 9, 8)},
            {"id_tarjeta": 4, "color": "amarilla", "minuto": 8, "numero_fecha": 3, "dia": date(2026, 9, 15)},
        ]
        statements = []
        with patch.object(_sanciones_automaticas, "fetch_one", return_value={"ci": 1234567}) as fetch_one, patch.object(
            _sanciones_automaticas, "fetch_all", return_value=cards
        ) as fetch_all, patch.object(
            _sanciones_automaticas,
            "execute",
            side_effect=lambda conn, sql, params=(): statements.append((sql, params)),
        ):
            _sanciones_automaticas.recalcular_sanciones_automaticas(object(), 7, 1234567)

        fetch_one.assert_called_once()
        fetch_all.assert_called_once()
        self.assertIn("p.estado = 'jugado'", fetch_all.call_args.args[1])
        self.assertIn("ORDER BY p.dia, p.numero_fecha, ta.minuto, ta.id_tarjeta", fetch_all.call_args.args[1])
        inserted = [params for sql, params in statements if sql.startswith("INSERT INTO sancion_jugador")]
        self.assertEqual(
            inserted,
            [
                (1234567, 7, "roja", 3),
                (1234567, 7, "acumulacion de amarillas", 4),
            ],
        )

    def test_recalculation_removes_stale_automatic_rows_but_not_manual_ones(self):
        statements = []
        with patch.object(_sanciones_automaticas, "fetch_one", return_value={"ci": 1234567}), patch.object(
            _sanciones_automaticas, "fetch_all", return_value=[]
        ), patch.object(
            _sanciones_automaticas,
            "execute",
            side_effect=lambda conn, sql, params=(): statements.append((sql, params)),
        ):
            _sanciones_automaticas.recalcular_sanciones_automaticas(object(), 7, 1234567)

        delete_sql, params = statements[0]
        self.assertIn("motivo IN (%s, %s)", delete_sql)
        self.assertEqual(params, (1234567, 7, "roja", "acumulacion de amarillas"))
        self.assertEqual(len(statements), 1)

    def test_planillero_card_write_uses_transactional_admin_connection(self):
        connection = object()
        with patch.object(tarjetas, "get_connection") as get_connection, patch.object(
            tarjetas, "exigir_partido_editable", return_value={"id_torneo": 7}
        ), patch.object(
            tarjetas, "fetch_one", return_value={"ok": 1}
        ), patch.object(
            tarjetas, "execute", return_value=SimpleNamespace(lastrowid=12)
        ), patch.object(
            tarjetas, "recalcular_sanciones_automaticas"
        ) as recalculate, patch.object(
            tarjetas, "_obtener", return_value={"id_tarjeta": 12}
        ):
            get_connection.return_value.__enter__.return_value = connection
            result = tarjetas.crear(
                5,
                TarjetaCreate(ci_jugador=1234567, minuto=15, color="roja"),
                SimpleNamespace(rol="planillero"),
            )

        self.assertEqual(result["id_tarjeta"], 12)
        get_connection.assert_called_once_with("administrador")
        recalculate.assert_called_once_with(connection, 7, 1234567)


if __name__ == "__main__":
    unittest.main()
