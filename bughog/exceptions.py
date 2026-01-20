class UserError(Exception):
    """
    Exception raised for errors that are due to user actions.
    """

    pass


class MissingParametersError(UserError):
    """
    Exception raised when required parameters are missing.
    """

    pass


class SystemError(Exception):
    """
    Exception raised for system-related errors.
    """

    pass


class OutOfMemoryError(SystemError):
    """
    Exception raised when BugHog runs out of memory.
    """

    pass
