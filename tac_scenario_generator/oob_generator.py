from settings import SUPPORTED_FORCES


def generate_oob(force):
    if force not in SUPPORTED_FORCES:
        raise ValueError(f'Unsupported force "{force}"')

    # TODO: actually generate a force for real. For now, this is hardcoded for
    # a Heer force to play with data structures.
    oob = {
        "force": force,
        "units": [
            {"type": "Rifle Platoon", "count": 2},
            {"type": "MG42 Light Machinegun", "count": 1},
            {"type": "81mm Mortar", "count": 1},
            {"type": "SPW 250/1 Halftrack", "count": 1}
        ]
    }

    return oob
