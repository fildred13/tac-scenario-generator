import logging
import time
from pathlib import Path

import torch
import yaml
from adapters import get_adapter

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PIL').setLevel(logging.INFO)

logger = logging.getLogger(__name__)


def main():
    # The script currently assumes that the user will navigate to the game
    # window after initializing the script, to simplify development. We'll want
    # to replace this with something which automatically maximizes the game in
    # the future. This sleep provides the user time to do that. In the future,
    # we'd probably want to prompt the user which screen to navigate to
    # depending on which game they're playing, and then wait for the user to
    # press a key to continue.
    print(
        'Script starting. Please navigate to the game now, and wait until '
        'the tool has finished populating units into the game.'
    )
    time.sleep(5)

    # For now, this tool only supports Combat mission games, and only supports
    # "generate forces and populate into game" mode. Thus, the main script does
    # that directly. Can make this more sophisticated and build a proper
    # interface when needed.

    # read the input yaml into memory.
    # TODO: nasty hack to read the input from a hardcoded location. works for now.
    project_directory = Path(__file__).resolve().parent.parent
    with open(project_directory / 'input.yaml', 'r') as f:
        run_config = yaml.safe_load(f)

    # determine the game we are operating on
    game = run_config['game']

    # load the appropriate adapter class
    adapter_class = get_adapter(game)
    adapter = adapter_class()

    # call the generate_and_populate() method
    adapter.generate_and_populate(run_config)

    # TODO: add a simple audio indicator when the script has completed or
    # error'd out.


if __name__ == "__main__":
    if not torch.cuda.is_available():
        logger.warn('CUDA is not available to Torch. Script may run slowly.')
    main()
