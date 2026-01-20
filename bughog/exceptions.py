class UserError(Exception):
    """
    Exception raised for errors that are due to user actions.
    """
    pass


class MissingParametersException(UserError):
    """
    Exception raised when required parameters are missing.
    """
    pass
