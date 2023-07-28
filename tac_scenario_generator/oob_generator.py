from settings import SUPPORTED_FORCES


def generate_oob(force):
    if force not in SUPPORTED_FORCES:
        raise ValueError(f'Unsupported force "{force}"')

    # TODO: actually generate a force for real. For now, this is hardcoded for
    # a Heer force to play with data structures.
    # TODO: probably need to adjust this data structure (and the translated oobs) to account for multi-force oobs.
    # TODO: we will need to add the concept of "timing" so that reinforcement waves can be orchestrated.
    oob = {
        "force": force,
        "units": [
            {"name": "Rifle Platoon", "class": "infantry", "count": 2},
            {"name": "MG42 Light Machinegun", "class": "support", "count": 1},
            {"name": "81mm Mortar", "class": "support", "count": 1},
            {"name": "SPW 250/1 Halftrack", "class": "vehicle", "count": 1}
        ]
    }

    return oob
