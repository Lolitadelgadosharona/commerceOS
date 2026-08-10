from typing import Any

from commerce_os.build.errors import BuildError
from commerce_os.decision.errors import DecisionError
from commerce_os.finance.errors import FinanceError
from commerce_os.governance.errors import GovernanceError
from commerce_os.intelligence.errors import IntelligenceError
from commerce_os.operations.errors import OperationsError
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def error_body(request: Request, code: str, message: str, details: list[Any] | None = None):  # type: ignore[no-untyped-def]
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", "unknown"),
            "details": details or [],
        }
    }


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(request, exc.code, exc.message),
    )


async def governance_error_handler(request: Request, exc: GovernanceError) -> JSONResponse:
    status_code = {
        "not_found": 404,
        "forbidden": 403,
        "invalid_state_transition": 409,
    }.get(exc.code, 400)
    return JSONResponse(
        status_code=status_code,
        content=error_body(request, exc.code, str(exc)),
    )


async def intelligence_error_handler(request: Request, exc: IntelligenceError) -> JSONResponse:
    status_code = {"not_found": 404, "forbidden": 403}.get(exc.code, 409)
    return JSONResponse(
        status_code=status_code,
        content=error_body(request, exc.code, str(exc)),
    )


async def build_error_handler(request: Request, exc: BuildError) -> JSONResponse:
    status_code = {"not_found": 404, "forbidden": 403, "invalid_state_transition": 409}.get(
        exc.code, 400
    )
    return JSONResponse(status_code=status_code, content=error_body(request, exc.code, str(exc)))


async def decision_error_handler(request: Request, exc: DecisionError) -> JSONResponse:
    status_code = {"forbidden": 403, "invalid_state_transition": 409}.get(exc.code, 400)
    return JSONResponse(status_code=status_code, content=error_body(request, exc.code, str(exc)))


async def operations_error_handler(request: Request, exc: OperationsError) -> JSONResponse:
    status_code = {"not_found": 404, "forbidden": 403}.get(exc.code, 409)
    return JSONResponse(status_code=status_code, content=error_body(request, exc.code, str(exc)))


async def finance_error_handler(request: Request, exc: FinanceError) -> JSONResponse:
    status_code = {"not_found": 404, "forbidden": 403}.get(exc.code, 409)
    return JSONResponse(status_code=status_code, content=error_body(request, exc.code, str(exc)))


async def integrity_error_handler(request: Request, _exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content=error_body(request, "conflict", "The resource conflicts with existing state."),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(part) for part in error["loc"]), "code": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_body(
            request,
            "validation_error",
            "The request did not satisfy the resource contract.",
            details,
        ),
    )
