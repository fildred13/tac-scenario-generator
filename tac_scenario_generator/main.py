import logging
import time

from adapters.combat_mission.api import populate_troops
from oob_generator import generate_oob
import torch

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PIL').setLevel(logging.INFO)

logger = logging.getLogger(__name__)


def main():
    # The script currently assumes that the user will navigate to the game
    # window after initializing the script, to simplify development. We'll want
    # to replace this with something which automatically maximizes the game in
    # the future. This sleep provides the user time to do that.
    print('Script starting. Please navigate to the game now, and wait at least 3 seconds before navigating away.')
    time.sleep(3)

    oob = generate_oob(force='heer')
    populate_troops(oob=oob)

    # TODO: add a simple audio indicator when the script has completed or
    # error'd out. Use the simpleaudio package, which is already added to the
    # project.


if __name__ == "__main__":
    print('#############')
    print(torch.cuda.is_available())

    #main()
