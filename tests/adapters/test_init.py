import pytest

from tac_scenario_generator.adapters import get_adapter
from tac_scenario_generator.adapters.combat_mission.adapter import \
    CombatMissionAdapter


def test_get_adapter_happy_case():
    adapter = get_adapter('cmak')
    assert isinstance(adapter, CombatMissionAdapter)


@pytest.mark.parametrize("game_id", [
    "bad_game_id"
])
def test_get_adapter_invalid_game_id(game_id):
    with pytest.raises(ValueError, match=".* Must be one of .*"):
        get_adapter(game_id)
