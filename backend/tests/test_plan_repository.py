import logging

import pytest
from postgrest import APIError

from app.repositories import plan_repository
from app.repositories.plan_repository import ErrorCrearPlan, PlanRepository


class RespuestaRPC:
    def execute(self):
        raise APIError(
            {
                "code": "23514",
                "message": 'new row violates check constraint "plan_sexo_check"',
                "details": "sensitive database details",
                "hint": "review the constraint",
            }
        )


class ClienteSupabaseFalso:
    def rpc(self, nombre, parametros):
        assert nombre == "crear_plan"
        assert parametros["p_usuario_id"] == 7
        return RespuestaRPC()


def test_error_rpc_se_registra_sin_incluir_detalles_de_fila(monkeypatch, caplog):
    monkeypatch.setattr(
        plan_repository, "cliente_supabase", ClienteSupabaseFalso()
    )

    with caplog.at_level(logging.ERROR, logger=plan_repository.__name__):
        with pytest.raises(ErrorCrearPlan, match="La base de datos rechazó"):
            PlanRepository().crear(7, {})

    assert "23514" in caplog.text
    assert "plan_sexo_check" in caplog.text
    assert "review the constraint" in caplog.text
    assert "sensitive database details" not in caplog.text
