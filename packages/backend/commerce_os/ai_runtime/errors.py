class AIRuntimeError(Exception):
    code = "invalid_state_transition"


class AIRuntimeScopeError(AIRuntimeError):
    code = "forbidden"


class AIRuntimeValidationError(AIRuntimeError):
    code = "validation_error"
