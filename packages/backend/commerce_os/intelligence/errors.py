class IntelligenceError(Exception):
    code = "intelligence_error"


class IntelligenceNotFoundError(IntelligenceError):
    code = "not_found"


class IntelligenceScopeError(IntelligenceError):
    code = "forbidden"


class IntelligenceValidationError(IntelligenceError):
    code = "invalid_intelligence_state"
