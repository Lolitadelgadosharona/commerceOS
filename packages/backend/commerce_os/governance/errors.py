class GovernanceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundError(GovernanceError):
    def __init__(self, message: str = "The governance resource was not found.") -> None:
        super().__init__("not_found", message)


class AuthorityError(GovernanceError):
    def __init__(self, message: str) -> None:
        super().__init__("forbidden", message)


class StateTransitionError(GovernanceError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_state_transition", message)
