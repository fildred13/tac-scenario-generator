def translate_oob(oob):
    """Given a TSG generic oob, generate a processed oob dictionary which is
    ready to be sent to the game engine.
    """
    # For now, since the oob is exactly of the form needed to pass to combat
    # mission, we can just pass it through. We'll need to expand this greatly
    # as we start to support more forces, games, etc.
    return oob
