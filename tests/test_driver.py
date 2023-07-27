from tac_scenario_generator.adapters.combat_mission import driver


def test_find_center_of_bounding_box():
    bbox = ((0, 0), (0,10), (20, 0), (20, 10))
    assert driver.find_center_of_bounding_box(bbox) == (10, 5)
