import logging

from tac_scenario_generator.adapters.combat_mission.driver import \
    send_units_to_game
from tac_scenario_generator.adapters.combat_mission.scenario_tools import \
    translate_oob

logger = logging.getLogger(__name__)


def populate_troops(oob):
    """Populates a Combat Mission: Beyond Overlord unit selection screen with
    an order of battle (oob). Requires that the screen is on the unit selection screen.
    """
    # translate oob to a combat mission compatible unit list.
    logger.info('Translating the oob to a combat mission compatible unit list')
    translated_oob = translate_oob(oob)
    logger.debug(f'Translated oob: {translated_oob}')

    # For each unit, send the needed clicks to add the units to the scenario.
    logger.info('Populating units into game engine.')
    send_units_to_game(translated_oob)
