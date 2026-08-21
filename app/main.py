from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.database import Base, engine
from app.routes import auth, projects, tasks
from app.utils.errors import error_content


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.include_router(auth.router)
    app.include_router(projects.router)
    app.include_router(tasks.router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Convert all HTTPExceptions to the standard error envelope."""
        try:
            phrase = HTTPStatus(exc.status_code).phrase  # e.g. "Not Found"
        except ValueError:
            phrase = "error"
        code = phrase.lower().replace(" ", "_")  # e.g. "not_found"
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_content(code, message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Convert validation errors to the standard error envelope."""
        errors = exc.errors()
        if errors:
            first = errors[0]
            message = first.get("msg", "Invalid request data")
        else:
            message = "Invalid request data"
        return JSONResponse(
            status_code=422,
            content=error_content("validation_error", message),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Convert database integrity errors to the standard error envelope."""
        return JSONResponse(
            status_code=409,
            content=error_content("conflict", "Database integrity error"),
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
