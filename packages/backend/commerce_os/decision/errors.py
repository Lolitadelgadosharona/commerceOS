class DecisionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class DecisionScopeError(DecisionError):
    def __init__(self, message: str) -> None:
        super().__init__("forbidden", message)


class DecisionStateError(DecisionError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_state_transition", message)
