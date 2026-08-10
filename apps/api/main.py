from commerce_os.build.errors import BuildError
from commerce_os.governance.errors import GovernanceError
from commerce_os.intelligence.errors import IntelligenceError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from apps.api.errors import (
    ApiError,
    api_error_handler,
    build_error_handler,
    governance_error_handler,
    integrity_error_handler,
    intelligence_error_handler,
    validation_error_handler,
)
from apps.api.middleware import request_context_middleware
from apps.api.routes import api_router

app = FastAPI(
    title="Commerce OS API",
    version="0.1.0",
    description="Sprint 001 integration contracts and customer foundation",
)
app.middleware("http")(request_context_middleware)
app.add_exception_handler(ApiError, api_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(BuildError, build_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(GovernanceError, governance_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(IntelligenceError, intelligence_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(IntegrityError, integrity_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
app.include_router(api_router)
