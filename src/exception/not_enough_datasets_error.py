class NotEnoughDatasetsError(Exception):
    """
    Excpetion for denoting that there are not enough datasets to be analyzed.
    """
    def __init__(self, message: str):
        super().__init__(self, message)