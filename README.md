# tac-scenario-generator
Toolset for generating tactical scenarios without the player knowing all the details

## Development Environment

This project is only tested on Windows, on a client which has a display device,
due to the fact that it must run against a video game which is also running. At
present, it is only tested on a Windows machine with a CUDA-capable graphics
card.

This project uses poetry for dependency management. First, install poetry
according to the poetry documentation. Then execute the following command to
install all project dependencies.

```bash
poetry install --with dev,codestyle --sync
```

See the poetry documentation for more information about adding and updating
dependencies.

The only other tool which must be installed on the host system is `tox` for
running unit tests and linting. The unit tests and linting must be run manually
at this time, because we cannot easily set up CI due to the fact that pyautogui
gets upset if there is no driver to talk to. Install tox, and run the tests and
lint with:

```bash
tox
```

Run the script itself like so.

```
poetry run python ./tac_scenario_generator/main.py
```
