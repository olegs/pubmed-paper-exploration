class HttpError(Exception):
    """
    Class for exceptions caused by non-200 status codes.
    """

    def __init__(self, message: str):
        super().__init__(self, message)
