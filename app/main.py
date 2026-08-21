from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.database import Base, engine
from app.routes import auth, projects, tasks
from app.utils.errors import error_response


STATUS_CODE_TO_ERROR_CODE = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    500: "internal_server_error",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(tasks.router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Normalize all HTTPExceptions into the standard error envelope."""
        code = STATUS_CODE_TO_ERROR_CODE.get(exc.status_code, "error")
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return error_response(code=code, message=message, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Flatten FastAPI validation errors into the standard error envelope."""
        errors = exc.errors()
        parts = []
        for err in errors:
            loc = " -> ".join(str(l) for l in err["loc"] if l != "body")
            parts.append(f"{loc}: {err['msg']}" if loc else err["msg"])
        message = "; ".join(parts)
        return error_response(code="validation_error", message=message, status_code=422)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Convert database integrity errors into the standard error envelope."""
        return error_response(
            code="integrity_error",
            message="Database integrity error",
            status_code=409,
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
