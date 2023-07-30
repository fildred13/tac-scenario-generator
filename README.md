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

Run the application itself by first making any desired changes to input.yaml in
the project root directory, navigating to the unit selection screen in Combat
Mission, and then running the following command:

```
poetry run python ./tac_scenario_generator/main.py
```

It will read the input file, generate a force list for each side (which gets
output as a debug artifact), ask you to navigate to the unit selection screen,
and then asks you to wait while it enters the selected forces. It will navigate
back to the scenario screen after it is complete. At present, there isn't
really any error handling, so if it crashes it will stay stuck on the unit
selection screen.
