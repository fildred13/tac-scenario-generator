from combat_mission.driver import find_and_click_target_text

import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    target_text = "Volksgrenadier Rifle Platoon"
    find_and_click_target_text(target_text)
