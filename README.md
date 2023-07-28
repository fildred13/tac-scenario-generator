# tac-scenario-generator
Toolset for generating tactical scenarios without the player knowing all the details

## Development Environment

This project uses poetry for dependency management. First, install poetry
according to the poetry documentation. Then execute the following command to
install all project dependencies.

```bash
poetry install --with dev,codestyle --sync
```

See the poetry documentation for more information about adding and updating
dependencies.

The only other tool which must be installed on the host system is `tox` for
running unit tests and linting. Install tox, and run the tests and lint with:

```bash
tox
```

At present, you must install torch manually, because EasyOCR requires this and
for some reason it doesn't install as part of EasyOCR. EasyOCR just links to
the pytorch docs for isntructions: https://pytorch.org/

Run the script itself like so. Notice that in this example I show what I'm
actually doing, which is running this through Powershell but using wsl (windows
subsystem for linux) to make it easy to call. It seems I have to call this from
windows because the actual WSL doesn't seem to have access to the display to
interact with it:

```
wsl poetry run python ./tac_scenario_generator/main.py
```
