from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db
from app.routes import auth, projects, tasks


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

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409, content={"detail": "Database integrity error"}
        )

    @app.get("/health")
    def health(db: Session = Depends(get_db)):
        """Health check endpoint that verifies database connectivity.

        Returns:
            200 with {"status": "ok", "database": "ok"} when the DB is reachable.
            503 with {"status": "degraded", "database": "error"} when the DB query fails.
        """
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ok", "database": "ok"}
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "database": "error"},
            )

    return app


app = create_app()
