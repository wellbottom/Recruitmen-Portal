from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {exc}",
        ) from exc

    return {"status": "ok"}
