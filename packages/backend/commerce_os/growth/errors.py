class GrowthError(Exception):
    def __init__(self, message: str, code: str = "invalid_state_transition") -> None:
        self.code = code
        super().__init__(message)
