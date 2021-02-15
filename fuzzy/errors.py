class AnticipatedError(Exception):
    """An error we expected."""


class UnableToComply(AnticipatedError):
    """We understood what the user wants, but can't."""

    TEXT = "Unable to comply."


class Unauthorized(AnticipatedError):
    """We understood what the user wants, but they aren't allowed to do it."""

    TEXT = "Unauthorized."


class PleaseRestate(AnticipatedError):
    """We didn't understand what the user wants."""

    TEXT = "Please restate query."
