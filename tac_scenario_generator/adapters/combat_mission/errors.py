class ScreenStateError(Exception):
    """Raised when the driver cannot execute a command because the current screen state would not allow it."""
    pass
