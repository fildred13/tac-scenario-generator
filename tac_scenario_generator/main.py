from adapters.combat_mission.api import populate_troops
from oob_generator import generate_oob

import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    oob = generate_oob(force='heer')
    populate_troops(oob=oob)


if __name__ == "__main__":
    main()
    target_text = "Volksgrenadier Rifle Platoon"
    find_and_click_target_text(target_text)
