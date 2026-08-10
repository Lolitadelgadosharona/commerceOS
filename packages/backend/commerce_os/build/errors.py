class BuildError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class BuildNotFoundError(BuildError):
    def __init__(self, message: str) -> None:
        super().__init__("not_found", message)


class BuildScopeError(BuildError):
    def __init__(self, message: str) -> None:
        super().__init__("forbidden", message)


class BuildStateError(BuildError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_state_transition", message)
