class FinanceError(ValueError):
    def __init__(self, message: str, code: str = "invalid_state_transition") -> None:
        super().__init__(message)
        self.code = code
