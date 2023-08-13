from tac_scenario_generator.adapters.combat_mission.driver import \
    CombatMissionDriver


def test_find_center_of_bounding_box():
    driver = CombatMissionDriver('cmak')
    bbox = ((0, 0), (0, 10), (20, 0), (20, 10))
    assert driver._find_center_of_bounding_box(bbox) == (10, 5)
