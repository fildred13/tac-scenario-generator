from tac_scenario_generator.adapters.combat_mission.adapter import CombatMissionAdapter


def get_adapter(game_id):
    """Given a game id as a string, return the matching adapter class. Raises a
    ValueError if the game_id is not recognized.
    """
    adapters = {
        'cmbo': CombatMissionAdapter,
        'cmbb': CombatMissionAdapter,
        'cmak': CombatMissionAdapter
    }
    try:
        return adapters[game_id](game_id)
    except KeyError:
        raise ValueError(f'Unrecognized game_id {game_id}. Must be one of {adapters.keys()}')
